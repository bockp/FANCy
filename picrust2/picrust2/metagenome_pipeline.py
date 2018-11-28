#!/usr/bin/env python

from __future__ import division

__copyright__ = "Copyright 2018, The PICRUSt Project"
__license__ = "GPL"
__version__ = "2.0.0-b.3"

import biom
import pandas as pd
from pandas.util.testing import assert_frame_equal
import numpy as np
from os import path
from joblib import Parallel, delayed
from picrust2.util import (biom_to_pandas_df, make_output_dir,
                           three_df_index_overlap_sort)


def run_metagenome_pipeline(input_biom,
                            function,
                            marker,
                            max_nsti,
                            out_dir='metagenome_out',
                            proc=1,
                            output_normfile=False):
    '''Main function to run full metagenome pipeline. Meant to run modular
    functions largely listed below. Will return predicted metagenomes
    straitifed and unstratified by contributing genomes (i.e. taxa).'''

    # Read in input table of sequence abundances and convert to pandas df.
    study_seq_counts = biom_to_pandas_df(biom.load_table(input_biom))

    # Read in predicted function and marker gene abundances.
    pred_function = pd.read_table(function, sep="\t", index_col="sequence")
    pred_marker = pd.read_table(marker, sep="\t", index_col="sequence")

    pred_function.index = pred_function.index.astype(str)
    pred_marker.index = pred_marker.index.astype(str)

    # Initialize empty pandas dataframe to contain NSTI values.
    nsti_val = pd.DataFrame()

    # If NSTI column present then remove all rows with value above specified
    # max value. Also, remove NSTI column (in both dataframes).
    if "metadata_NSTI" in pred_function.columns:

        pred_function = pred_function[pred_function['metadata_NSTI'] <= max_nsti]
        nsti_val = pred_function[['metadata_NSTI']]
        pred_function.drop('metadata_NSTI', axis=1, inplace=True)

    if "metadata_NSTI" in pred_marker.columns:
        pred_marker = pred_marker[pred_marker['metadata_NSTI'] <= max_nsti]

        nsti_val = pred_marker[['metadata_NSTI']]

        pred_marker.drop('metadata_NSTI', axis=1, inplace=True)

    # Re-order predicted abundance tables to be in same order as study seqs.
    # Also, drop any sequence ids that don't overlap across all dataframes.
    study_seq_counts, pred_function, pred_marker = three_df_index_overlap_sort(study_seq_counts,
                                                                               pred_function,
                                                                               pred_marker)

    # Create output directory if it does not already exist.
    make_output_dir(out_dir)

    # Create normalized sequence abundance filename if outfile specified.
    if output_normfile:
        norm_output = path.join(out_dir, "seqtab_norm.tsv")
    else:
        norm_output = None

    # Normalize input study sequence abundances by predicted abundance of
    # marker genes and output normalized table if specified.
    study_seq_counts = norm_by_marker_copies(input_seq_counts=study_seq_counts,
                                             input_marker_num=pred_marker,
                                             norm_filename=norm_output)

    # If NSTI column input then output weighted NSTI values.
    if not nsti_val.empty:
        weighted_nsti_out = path.join(out_dir, "weighted_nsti.tsv")
        weighted_nsti = calc_weighted_nsti(seq_counts=study_seq_counts,
                                           nsti_input=nsti_val,
                                           outfile=weighted_nsti_out)

    # Get predicted function counts by sample, stratified by contributing
    # genomes and also separately unstratified.
    return(funcs_by_sample(input_seq_counts=study_seq_counts,
                           input_function_num=pred_function,
                           proc=proc))


def calc_weighted_nsti(seq_counts, nsti_input, outfile=None):
    '''Will calculate weighted NSTI values given sequence count table and NSTI
    value for each sequence. Will output these weighted values to a file if
    output file is specified.'''

    nsti_mult = seq_counts.mul(nsti_input.metadata_NSTI, axis=0)

    # Get column sums divided by total abundance per sample.
    weighted_nsti = pd.DataFrame(nsti_mult.sum(axis=0)/seq_counts.sum(axis=0))

    weighted_nsti.columns = ["weighted_NSTI"]

    # Write to outfile if specified.
    if outfile:
        weighted_nsti.to_csv(path_or_buf=outfile, sep="\t", header=True,
                             index_label="sample")

    return(weighted_nsti)


def norm_by_marker_copies(input_seq_counts,
                          input_marker_num,
                          norm_filename=None,
                          round_decimal=2):

    '''Divides sequence counts (which correspond to amplicon sequence
    variants) by the predicted marker gene copies for each sequence. Will write
    out the normalized table if option specified.'''

    input_seq_counts = input_seq_counts.div(input_marker_num.loc[
                                                input_seq_counts.index.values,
                                                input_marker_num.columns.values[0]],
                                            axis="index")


    input_seq_counts = input_seq_counts.round(decimals=round_decimal)

    # Output normalized table if specified.
    if norm_filename:
        input_seq_counts.to_csv(path_or_buf=norm_filename,
                                index_label="sequence",
                                sep="\t")

    return(input_seq_counts)


def funcs_by_sample(input_seq_counts, input_function_num, proc=1):
    '''Function that reads in study sequence abundances and predicted
    number of gene families per study sequence's predicted genome. Will
    return abundance of functions contributed by each study sequence per
    sample in pandas dataframe and another dataframe in unstratified format.'''

    # Sample ids are taken from sequence abundance table.
    sample_ids = input_seq_counts.columns.values

    # Loop through all samples and get predicted functional abundances
    # after multiplying each contributing sequence by the abundance in
    # the sequence abundance dataframe.
    if proc > 1:
        strat_out = Parallel(n_jobs=proc)(delayed(
                            func_by_seq_abun)(
                            input_seq_counts[sample],
                            input_function_num)
                            for sample in sample_ids)
    else:
        # Run in basic loop if only 1 processor specified.
        strat_out = []

        for sample in sample_ids:
            strat_out += [func_by_seq_abun(input_seq_counts[sample],
                                           input_function_num)]

    # Build dataframe from list of series (one per sample).
    strat_out_df = pd.DataFrame(strat_out).transpose()

    # Replace all NaN values with 0s.
    strat_out_df.fillna(0, inplace=True)

    # Set column names to be sample ids.
    strat_out_df.columns = sample_ids

    strat_out_df.reset_index(inplace=True)

    # Sum rows by function id for unstratified output and set index labels
    # equal to function ids (remove "sequence" column first).
    unstrat_out_df = strat_out_df.copy()

    unstrat_out_df = pd.pivot_table(unstrat_out_df.drop('sequence', 1),
                                    index="function",
                                    aggfunc=np.sum)

    return(strat_out_df, unstrat_out_df)


def func_by_seq_abun(sample_seq_counts, func_abun):
    '''Given the abundances of sequences in a sample (as a pandas series) and
    the predicted functions of those sequences (as a pandas dataframe), this
    function will return the functional abundances after multiplying the
    abundances of functions contributed by a sequence by that sequence's
    abundance. Will return a long-form dataframe with 3 columns: function,
    sequence, and count. Note that this function assumes that the order of the
    sequences is the same in both the input series and the dataframe of
    function abundances.'''

    func_abun_depth = func_abun.mul(sample_seq_counts, axis=0)

    # Set index labels (sequence ids) to be new column.
    func_abun_depth["sequence"] = func_abun_depth.index.values

    # Convert from wide to long table format (only columns for sequence,
    # function, and count).
    func_abun_depth_long = pd.melt(func_abun_depth, id_vars=["sequence"],
                                   var_name="function", value_name="count")

    # Remove all rows with counts of zero.
    func_abun_depth_long = func_abun_depth_long[func_abun_depth_long['count'] > 0]

    func_abun_depth_long.transpose()

    # Set index labels to be sequence and function columns.
    func_abun_depth_long = func_abun_depth_long.set_index(keys=["function",
                                                                "sequence"])

    # Convert long-form pandas dataframe to series and return.
    return(func_abun_depth_long["count"])
