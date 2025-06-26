import argparse
import polars as pl
import re
import sys
from typing import List

# For the moment we are using a file with the protein coding genes in hg19.
# Note that it may be extended to include other type og genes such as lncRNA, miRNA, etc.


# ------------------------------ #
# Utilities and helper functions #
# ------------------------------ #


def columns_exist(df               : pl.DataFrame = None,
                  required_columns : List[str] = None, 
                  label            : str = "DataFrame"):
    """ Check if the required columns are present in a Polars DataFrame.
    Args:
        df (pl.DataFrame): The DataFrame to check.
        required_columns (list): List of required column names.
        label (str): Label for the DataFrame, used in error messages.
    Raises:
        ValueError: If any required columns are missing.
    """
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")



def columns_noempty(df: pl.DataFrame, colnames: list[str]):
    """
    Check that each column in `colnames` contains at least one valid value.
    For string columns: must not be null, empty, or "NA".
    For numeric columns: must not be null.
    Exits if any column fails this condition.
    """
    for colname in colnames:
        dtype = df.schema[colname]
        
        if dtype == pl.Utf8:
            valid_rows = df.filter(
                pl.col(colname).is_not_null() &
                (pl.col(colname).str.strip_chars() != "") &
                (pl.col(colname).str.to_lowercase() != "na")
            )
        else:
            # For numeric or other types, just check non-null
            valid_rows = df.filter(pl.col(colname).is_not_null())

        if valid_rows.is_empty():
            print(f"No valid values found in the '{colname}' column. Exiting.")
            sys.exit(1)



def sep_columns_v(df : pl.DataFrame, sep : str = ",", colname : str = None) -> pl.DataFrame:
    """
    Explode a dataframe from a str column containing a separator.
    Separates the column in a vertical manner, creating new rows for each split part.

    Returns the pl.DataFrame with the column exploded.
    Args:
        df (pl.DataFrame): Input DataFrame.
        sep (str): Separator to use for splitting.
        colname (str): Name of the column to explode.
    Returns:
        pl.DataFrame: DataFrame with the specified column exploded into multiple rows.
    """
    
    tmp_column = "Tmp_column"
    
    # Step 1: Split the 'sep'-separated names into lists
    df = df.with_columns( pl.col(colname).str.split(sep).alias(tmp_column) )

    # Step 2: Explode the lists into individual rows
    df_exploded = df.explode(tmp_column)

    # Rename the exploded column
    df_exploded = df_exploded.drop(colname).rename({tmp_column : colname})

    return(df_exploded)


def sep_columns_h(df          : pl.DataFrame = None,
                  column      : str = None,
                  delim       : str = ":",
                  max_splits  : int = None,
                  new_cols    : List[str] = None,
                  keep_column : bool = True) -> pl.DataFrame:
    """
    This function splits a specified column in a Polars DataFrame into multiple new columns based on a delimiter.
    Separates the column in a horizontal manner, creating new columns for each split part.

    Args:
        df (pl.DataFrame): Input DataFrame.
        column (str): Name of the column to split.
        delim (str): Delimiter to use for splitting.
        max_splits (int, optional): Maximum number of splits. If None, split all.
        new_cols (List[str], optional): List of new column names. If None, defaults to column_{i+1}.
    Returns:
        pl.DataFrame: DataFrame with the specified column split into multiple new columns.
    """

    # Build the split expression
    if max_splits is None:
        split_expr = pl.col(column).str.split(delim)
    else:
        split_expr = pl.col(column).str.splitn(delim, max_splits)

    # Temporary column to hold split parts
    tmp_col = "__tmp_split__"

    # Apply the split and convert to struct in one step
    df = df.with_columns( split_expr.alias(tmp_col) )

    # Get number of resulting columns (by inspecting first row)
    n_fields = len(df[tmp_col][0])

    # Generate default field names if not provided
    if new_cols is None:
        new_cols = [f"{column}_{i+1}" for i in range(n_fields)]
    elif len(new_cols) != n_fields:
        raise ValueError(f"Expected {n_fields} new field names, got {len(new_cols)}")

    # Do the split and remove the temporary column
    df = (df.with_columns( pl.col(column)
                             .str.split_exact(delim, n_fields)
                             .struct.rename_fields(new_cols)
                             .alias("fields")
            )   
            .unnest("fields")
            .drop("__tmp_split__")
        )
    
    if not keep_column:
        df = df.drop(column)
    
    return df



def parse_fusion_info(fusion_str):
    """
    Parses the fusion string to extract gene names, chromosome names, and positions.

    Examples of fusion_str:
    - 'NRG1/ATP1B1 (chr8:32474403-chr1:169080608)'
    - 'FGFR3-IGF2 (chr3:1809089-chr11:2153330)'
    """
    gene_part, coord_part = fusion_str.split(" ", 1)
    coord_match = re.search(r"\((chr[^\)]+)\)", coord_part)

    if not coord_match:
        return [None] * 6  # gene1, chrom1, pos1, gene2, chrom2, pos2

    coords = coord_match.group(1)
    genes = re.split(r"[-/]", gene_part)
    chr1, pos1, chr2, pos2 = None, None, None, None

    chr_pos = re.split(r"[:-]", coords)
    chrA, posA, chrB, posB = chr_pos[0], int(chr_pos[1]), chr_pos[2], int(chr_pos[3])

    if "/" in gene_part:
        gene1, gene2 = genes[1], genes[0]  # reverse
        chrom1, pos1, chrom2, pos2 = chrB, posB, chrA, posA
    elif "-" in gene_part:
        gene1, gene2 = genes[0], genes[1]
        chrom1, pos1, chrom2, pos2 = chrA, posA, chrB, posB
    else:
        return [None] * 6

    return gene1, chrom1, pos1, gene2, chrom2, pos2



def process_mutation_summary(summary_file : pl.dataframe = None) -> pl.DataFrame:
    """
    Process the summary mutation file and sample mutation file to create a TSV output.

    All processing related to this file should be done here.
    Args:
        summary_file (str): Path to the summary mutation file.
    Returns:
        pl.DataFrame: Processed DataFrame containing fusion events.
    """
     
    # Read summary mutations
    print(f"; Reading summary mutation table : {summary_file}")
    summary = pl.read_csv(summary_file, separator="\t", comment_prefix='#')

    # Check if the required columns are present and not empty
    required_columns = ["sample_id", "fusions"]
    columns_exist(summary, required_columns, label="Summary mutations")
    columns_noempty(summary, required_columns)
     
    # Explode the 'fusions' column to separate rows
    print(f"; Exploding 'fusions' column")
    summary = sep_columns_v(summary, sep="|", colname="fusions")

    # Split the 'fusions' column into multiple columns (genes and coordinates)
    print(f"; Splitting 'fusions' column into multiple columns")
    summary = summary.filter( (pl.col("fusions") !=  "NA") )
    summary = sep_columns_h(summary, "fusions", delim=" ", keep_column=False, new_cols = ["name", "coord", "other"])
    print(summary)

    # Select relevant columns
    summary = summary.select(['sample_id', "name", "coord"])
    return summary


def process_mutation_samples(mut_file : str = None) -> pl.DataFrame:
    """Process the sample mutation file to extract fusion events.

    The resulting dataframe contains twice the number of rows as the original,
    because each fusion event is represented in both orientations (gene1-gene2 and gene2-gene1).

    Args:
        mut_file (str): Path to the sample mutation file.
    Returns:
        pl.DataFrame: Processed DataFrame containing fusion events.
    """

    print(f"; Reading patient mutation table : {mut_file}")
    samples = pl.read_csv(mut_file, separator="\t", comment_prefix='#', null_values="N/A")

    # Check if the required columns are present
    required_columns = ["Sample_ID", "Alt_Split_Dedup", "Alt_Paired_Dedup"]
    columns_exist(samples, required_columns, label="Sample mutations")
    columns_noempty(samples, required_columns)

    # Select fusion events, filtering out those with no fusions
    # Select and rename relevant columns
    # Original filtered and selected DataFrame
    selected = (
        samples
        .filter(pl.col("Provisional_Event_Type") == "Fusion")
        .select([
            pl.col("Sample_ID").alias("sample_id"),
            pl.col("Gene_A").alias("gene1"),
            pl.col("Gene_B").alias("gene2"),
            pl.col("Chrom_A").alias("chrom1"),
            pl.col("Provisional_Event_Site_A").alias("pos1"),
            pl.col("Chrom_B").alias("chrom2"),
            pl.col("Provisional_Event_Site_B").alias("pos2"),
            pl.col("Alt_Split_Dedup").alias("split"),
            pl.col("Alt_Paired_Dedup").alias("span"),
        ])
    )

    # Create original coord string
    selected = selected.with_columns(
        pl.format(
            "({}:{}-{}:{})",
            pl.col("chrom1"),
            pl.col("pos1"),
            pl.col("chrom2"),
            pl.col("pos2")
        ).alias("coord")
    )

    # Create inverted version
    inverted = selected.select([
        pl.col("sample_id"),
        pl.col("gene2").alias("gene1"),
        pl.col("gene1").alias("gene2"),
        pl.col("chrom2").alias("chrom1"),
        pl.col("pos2").alias("pos1"),
        pl.col("chrom1").alias("chrom2"),
        pl.col("pos1").alias("pos2"),
        pl.col("split"),
        pl.col("span"),
    ]).with_columns(
        pl.format(
            "({}:{}-{}:{})",
            pl.col("chrom1"),
            pl.col("pos1"),
            pl.col("chrom2"),
            pl.col("pos2")
        ).alias("coord")
    )

    # Concatenate original + inverted
    samples = pl.concat([selected, inverted])
    return samples



def main(summary_file, sample_mut_file, gene_coord, output_file):

    # Process the summary mutation file
    summary_df = process_mutation_summary(summary_file)
    #print(summary_df)

    # Process the sample mutation file
    samples_df = process_mutation_samples(sample_mut_file)
    #print(samples_df)

    # Join the summary with the sample mutations
    fusions2export = (summary_df.join( samples_df,
                                      left_on  = "coord",
                                      right_on = "coord",
                                      how      = "inner")
                                .select([
                                    pl.col("chrom1"),
                                    pl.col("pos1"),
                                    pl.col("gene1"),
                                    pl.col("chrom2"),
                                    pl.col("pos2"),
                                    pl.col("gene2"),
                                    pl.col("name"),
                                    pl.col("split"),
                                    pl.col("span"),
                                    pl.lit(".").alias("strand1"),  # Default strand direction
                                    pl.lit(".").alias("strand2"),  # Default strand direction
                                    pl.lit("").alias("untemplated_insert"),  # Default untemplated insert
                                    pl.lit("").alias("comment")  # Default comment
                                ]))

    # Read hg19 protein coding gene table
    hg19_genes = (pl.read_csv(gene_coord, separator="\t")
                    .select([ pl.col("hgnc_symbol").alias("gene_name"),
                              pl.col("strand")])
                    .unique()
                 )
    hg19_genes = dict(hg19_genes.select("gene_name", "strand").iter_rows())


    fusions2export = fusions2export.with_columns( pl.col("gene1").map_elements(lambda g: hg19_genes.get(g), return_dtype=pl.String).alias("strand1"),
                                                  pl.col("gene2").map_elements(lambda g: hg19_genes.get(g), return_dtype=pl.String).alias("strand2")
    )

    # Create DataFrame and write to TSV
    fusions2export.write_csv(output_file, separator="\t")
    print(fusions2export)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SV summary TSV file.")
    parser.add_argument("-s", "--summary_file", required=True, help="Path to summary mutations file")
    parser.add_argument("-m", "--sample_mut_file", required=True, help="Path to sample mutations file")
    parser.add_argument("-g", "--gene_coord", required=True, help="Path to gene coordinate file")
    parser.add_argument("-o", "--output", default="output.tsv", help="Output TSV file name (default: output.tsv)")

    args = parser.parse_args()
    main(args.summary_file, args.sample_mut_file, args.gene_coord, args.output)
