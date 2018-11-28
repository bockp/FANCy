#ifndef GENESIS_TAXONOMY_FORMATS_TAXOPATH_GENERATOR_H_
#define GENESIS_TAXONOMY_FORMATS_TAXOPATH_GENERATOR_H_

/*
    Genesis - A toolkit for working with phylogenetic data.
    Copyright (C) 2014-2017 Lucas Czech

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
    Lucas Czech <lucas.czech@h-its.org>
    Exelixis Lab, Heidelberg Institute for Theoretical Studies
    Schloss-Wolfsbrunnenweg 35, D-69118 Heidelberg, Germany
*/

/**
 * @brief
 *
 * @file
 * @ingroup taxonomy
 */

#include <string>
#include <vector>

namespace genesis {
namespace taxonomy {

// =================================================================================================
//     Forward Declarations
// =================================================================================================

class Taxon;
class Taxopath;

// =================================================================================================
//     Taxopath Generator
// =================================================================================================

/**
 * @brief Helper class to generate a taxonomic path string from a Taxopath object
 * or a Taxon.
 *
 * This class bundles the parameters used for generating a taxonomic path string.
 * This is needed in order to allow customization of the generation process.
 * The result of the process is a string representation of the taxonomic path, with all
 * names of the super-taxa of the given taxon (and the taxon itself), concatenated using the
 * @link delimiter( std::string const& value ) delimiter()@endlink.
 *
 * For example, the Taxon
 *
 *     Tax_1
 *         Tax_2
 *             Tax_2
 *                 Tax_4
 *
 * might result in a string representation
 *
 *     Tax_1;Tax_2;;Tax_4;
 *
 * The same result is also obtained from a Taxopath `[ "Tax_1", "Tax_2", "Tax_2", "Tax_4" ]`.
 */
class TaxopathGenerator
{
public:

    // -------------------------------------------------------------------------
    //     Constructors and Rule of Five
    // -------------------------------------------------------------------------

    TaxopathGenerator()  = default;
    ~TaxopathGenerator() = default;

    TaxopathGenerator( TaxopathGenerator const& ) = default;
    TaxopathGenerator( TaxopathGenerator&& )      = default;

    TaxopathGenerator& operator= ( TaxopathGenerator const& ) = default;
    TaxopathGenerator& operator= ( TaxopathGenerator&& )      = default;

    // -------------------------------------------------------------------------
    //     Generating
    // -------------------------------------------------------------------------

    std::string to_string(   Taxopath const& taxopath ) const;
    std::string operator() ( Taxopath const& taxopath ) const;

    std::string to_string(   Taxon const& taxon ) const;
    std::string operator() ( Taxon const& taxon ) const;

    // -------------------------------------------------------------------------
    //     Properties
    // -------------------------------------------------------------------------

    TaxopathGenerator& delimiter( std::string const& value );
    std::string           delimiter() const;

    TaxopathGenerator& trim_nested_duplicates( bool value );
    bool                  trim_nested_duplicates() const;

    TaxopathGenerator& append_delimiter( bool value );
    bool                  append_delimiter() const;

    // -------------------------------------------------------------------------
    //     Data Members
    // -------------------------------------------------------------------------

private:

    std::string delimiter_              = ";";
    bool        trim_nested_duplicates_ = false;
    bool        append_delimiter_       = false;

};

} // namespace taxonomy
} // namespace genesis

#endif // include guard
