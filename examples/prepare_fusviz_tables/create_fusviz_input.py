import argparse
import polars as pl
import re
import sys
from typing import List


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


def column_noempty(df      : pl.DataFrame = None, 
                         colname : str = None):
    """
    Check if a column in a DataFrame is not empty.
    """

    # Check if at least one fusion is present in column 'fusions'
    # otherwise, ends the script
    valid_colname = df.filter(
        pl.col(colname).is_not_null()                      # not null
        & (pl.col(colname).str.strip_chars() != "")        # not empty after trimming
        & (pl.col(colname).str.to_lowercase() != "na")     # not "na"
    )

    if valid_colname.is_empty():
        print(f"No valid values found in the '{colname}' column. Exiting.")
        sys.exit(1)            # or `return` inside a function
        




def separate_columns(df : pl.DataFrame, sep : str = ",", colname : str = None) -> pl.DataFrame:
    """
    Explode a dataframe from a str column containing a separator.

    Returns the pl.DataFrame with the column exploded.
    """
    
    tmp_column = "Tmp_column"
    
    # Step 1: Split the 'sep'-separated names into lists
    df = df.with_columns( pl.col(colname).str.split(sep).alias(tmp_column) )

    # Step 2: Explode the lists into individual rows
    df_exploded = df.explode(tmp_column)

    # Rename the exploded column
    df_exploded = df_exploded.drop(colname).rename({tmp_column : colname})

    return(df_exploded)




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


def read_tsv_ignore_comments(path):
    with open(path, 'r') as f:
        lines = [line for line in f if not line.startswith('#')]
    return pl.read_csv(
        source=lines,
        separator="\t"
    )


def main(summary_file, sample_mut_file, output_file):
    
    # Read files with comment lines skipped
    print(f"; Reading summary mutation table")
    summary = pl.read_csv(summary_file, separator="\t", comment_prefix='#')

    # Check if the required columns are present and not empty
    required_columns = ["sample_id", "fusions"]
    columns_exist(summary, required_columns, label="Summary mutations")
    column_noempty(summary, "fusions")
    
    # Explode the 'fusions' column to separate rows
    print(f"; Exploding 'fusions' column")
    summary = separate_columns(summary, sep="|", colname="fusions")
    print(summary)
    
    

    



    # print(f"; Reading patient mutation table")
    # samples = pl.read_csv(sample_mut_file, separator="\t", comment_prefix='"')

    # # Check if the required columns are present
    # required_columns = ["Sample_ID", "Alt_Split_Dedup", "Alt_Paired_Dedup"]
    # check_required_columns_pl(samples, required_columns, label="Sample mutations")



    # rows = []

    # for row in summary.iter_rows(named=True):
    #     sample_id = row["sample_id"]
    #     fusion_str = row["fusions"]

    #     if not fusion_str or fusion_str.strip().lower() == "na":
    #         continue

    #     gene1, chrom1, pos1, gene2, chrom2, pos2 = parse_fusion_info(fusion_str)

    #     # Find corresponding row in sample mutations
    #     sample_row = samples.filter(pl.col("Sample_ID") == sample_id)
    #     if sample_row.is_empty():
    #         continue

    #     sample_row = sample_row[0]
    #     split = sample_row.get("Alt_Split_Dedup", 0)
    #     span = sample_row.get("Alt_Paired_Dedup", 0)

    #     rows.append({
    #         "chrom1": chrom1,
    #         "pos1": pos1,
    #         "gene1": gene1,
    #         "chrom2": chrom2,
    #         "pos2": pos2,
    #         "gene2": gene2,
    #         "name": sample_id,
    #         "split": split,
    #         "span": span,
    #         "strand1": "+",
    #         "strand2": "+",
    #         "untemplated_insert": ".",
    #         "comment": "."
    #     })

    # # Create DataFrame and write to TSV
    # df_out = pl.DataFrame(rows)
    # df_out.write_csv(output_file, separator="\t")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SV summary TSV file.")
    parser.add_argument("summary_file", help="Path to summary mutations file")
    parser.add_argument("sample_mut_file", help="Path to sample mutations file")
    parser.add_argument("-o", "--output", default="output.tsv", help="Output TSV file name")

    args = parser.parse_args()
    main(args.summary_file, args.sample_mut_file, args.output)

