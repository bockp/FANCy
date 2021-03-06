#!/bin/bash                                                                                                                                                            

# get command line inputs                                                                                                                                              

# expected input:                                                                                                                                                      
# FANCy-otu.sh otuTableFile otuSeqsFile matchfilesDir logDir outDir metaDataVectorFile pval normalizationOption condA condB
# example:
# FANCy-otu.sh otudir/otuTable.txt otudir/otuSeqs.fasta matchfilesDir log_H output_H HumanApeMetadata.csv 0.05 "tss" "no" "yes"                                                             
# (-p pval) -n normalization\                                                                                       
usage="\nUsage: $0 -z bamzip (-m matchfilesDir) (-l logDir) (-o outDir) -v metaDataVectorFile (-p pval) -n normalizationOption -a condA -b condB\n"

if [ $# -lt 5 ]; then
    echo $usage
    echo "\nelements in parenthesis are optional. default P value is 0.05\n"
    exit 1
fi

# testing that the obligatory parameters are indeed present:                                                       
# first set all non-optional argument values to False, with the optional arguments having their default values.    
# After the getopts processing we can then test if any of the parameters are still set to False, and print the correct error message is so.       
# normalization -> "tss" for Total Sum Scaling, "uqs" for Upper Quartile Scaling, any other value for no scaling.                                                                                                                        

bamzip=false;
match="matchfiles";
log="log";
out="output";
meta=false;
pval=0.05;
option=false;
grp1=false;
grp2=false;


#process cmdline arguments                                                                                        

while getopts 'z:m:l:o:v:p:n:a:b:' c
do
    case $c in
        z) bamzip=$OPTARG;;
        m) match=$OPTARG;;
        l) log=$OPTARG;;
        o) out=$OPTARG;;
        v) meta=$OPTARG;;
        p) pval=$OPTARG;;
        n) option=$OPTARG;;
        a) grp1=$OPTARG;;
        b) grp2=$OPTARG;;
        \?) echo "invalid option: -$c $OPTARG" >&2; exit 1;;
    esac
done


# test that the obligatory command line arguments have been set.                                                   
# If yes, check that they are "correct" (file extensions, existing files, etc...)                                  

if [ "$bamzip" = false ];
then
    echo "The bamzip parameter is missing, please retry with the correct option included:"
    echo "-z bamzip.zip"
else
    if [ ! -f "$bamzip" ];
    then
        echo "Error: The given $bamzip file doesn't exist"
        exit 1;
    fi
fi

if [ "$meta" = false ];
then
    echo "The MetaData Vector parameter is missing, please retry with the correct option included:"
    echo "-v metaVector.csv"
else
    if [ ! -f "$meta" ];
    then
        echo "Error: The given metadataVector file doesn't exist"
	exit 1;
    fi

fi

if [ "$option" = false ];
then
    echo "The normalization parameter is missing, please retry with the correct option ('tss','uqs' or 'none') inc\
luded:"
    echo "-n normalizationOption"
fi


if [ "$grp1" = false ];
then
    echo "The first study group parameter is missing, please retry with the correct option included:"
    echo "-a grp1"
fi

if [ "$grp2" = false ];
then
    echo "The second study group parameter is missing, please retry with the correct option included:"
    echo "-b grp2"                                                                                                \

fi

if [ "$(echo $pval '>' 1.00 | bc -l)" -eq 1   -o "$(echo $pval '<' 0.00 | bc -l)" -eq 1   ];

then
    echo "Error: Invalid P value. must be between 1 and 0 !"
    exit 1;
fi

if ! grep -Fwq "$grp1" "$meta" 
then
    echo "The given GRP1 grouping variable ( $grp1 ) doesn't exist in the metadata vector file $meta"
    exit 1;

fi

if ! grep -Fwq "$grp2" "$meta" 
then
    echo "The given GRP2 grouping variable ( $grp2 ) doesn't exist in the metadata vector file $meta"
    exit 1;
fi




# Condition A and B MUST be the exact values desired, as written in the metadataVector File.

# The Metadata file must be a 2 column vector, one column containing the names of the samples,
#  the other containing the category that sample is in (ex: human -> yes, no)

SCRIPT=`realpath $0`
SCRIPTPATH=`dirname $SCRIPT`
snake="$SCRIPTPATH""/snakefile-bam"
taxa="ncbiDB/taxa.sqlite"
db="$SCRIPTPATH""/UNITEid"



 
# make any directories not automatically generated by the Snakemake pipeline, and copy the two otu files into the otu directory for processing.

mkdir -p ncbiDB
touch ncbiDB/taxa.sqlite


# replace the "." in file.zip with a space, then make into a list.
bamDir=(${bamzip//./ })
# use the fist element ("file" in "file.zip") as name of the BamDirectory
mkdir -p $bamDir
unzip $bamzip -d $bamDir


mkdir -p $out/tango







# For the local version, the total number of allowed samples:
# change this if you need more samples (though this Local limit should be largely sufficient)
allowed=300







# execute the snakemake pipeline using the OTU processing path, and the above options, directories and files.


snakemake -s $snake --config tango="$SCRIPTPATH" cur_dir="$SCRIPTPATH" bamdir="$bamDir"  output="$out" log="$log" ncbiDB="$taxa" pval="$pval" matchfiles="$match" metadata="$meta" option="$option" uniteDB="$db" GRP1="$grp1" GRP2="$grp2" allowed="$allowed";



#mv $out/pheatmap* $out/pheatmap.png
mv $out/pvals* $out/pvals.csv

sed -i '1iPathway_names' $out/pathwayAbundances.csv
sed -i 's/function/Taxon_ID/g' $log/species_by_sample.tsv
# 
