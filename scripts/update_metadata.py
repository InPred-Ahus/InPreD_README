import argparse


# Replace norwegian characters (upper and lower cases) by standard characters
def normalize_norsk_chars(text):
    replacements = {
        'Æ': 'Ae', 'æ': 'ae',
        'Ø': 'Oe', 'ø': 'oe',
        'Å': 'Aa', 'å': 'aa',
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text


# Note: the 'latin' encoding don't cause issues to read the metadata, however we must verify that other lines are not altered.
# Solution: use try-except with utf-8 and latin.
def safe_readlines(file_path):
    """Try reading a file with utf-8, then fall back to latin1 if needed."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin') as f:
            return f.readlines()

# This function reads the new PRONTO metadata file, convert the norwegian characters to standard ones and add the run ID values.
# Returns a string that is ready to be inserted in the master metadata table.
def process_new_meta(new_meta_path, new_run_id):

    # Replace all instances of norwegian special characters in the file
    def normalize_row(fields):
        return [normalize_norsk_chars(f) for f in fields]

    lines = safe_readlines(new_meta_path)

    if not lines:
        raise ValueError("File A is empty.")

    header = lines[0].strip().split('\t')
    data_lines = []

    for line in lines[1:]:
        fields = line.strip().split('\t')
        if len(fields) < len(header):
            continue  # Skip malformed lines
        fields = normalize_row(fields)
        fields[1] = new_run_id # Add run ID value in 2nd column
        data_lines.append('\t'.join(fields))

    return data_lines


# Updates the PRONTO metadata master table
# Comment the previous run, create a new batch with the PRONTO metadata of the current run ID
def update_meta_master(master_metapath, new_meta_lines, output_path):

    lines = safe_readlines(master_metapath)

    # Save header and commented lines before the header
    header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith('Sample_id'))
    pre_header = lines[:header_idx]
    header = lines[header_idx].strip()
    post_header_lines = lines[header_idx + 1:]

    # Update previous run batch
    # Set the Create_report column to 'N'
    updated_post_header = []
    for line in post_header_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            updated_post_header.append(stripped)
        else:
            parts = stripped.split('\t')
            if len(parts) >= 3:
                parts[2] = 'N'
                print(parts)
                updated_post_header.append('\t'.join(parts))
            else:
                updated_post_header.append(stripped)

    # Construct a new file by joining the header and comments + new metadata + updated previous run entries
    new_lines = []
    new_lines.extend([l.rstrip('\n') for l in pre_header])
    new_lines.append(header)
    new_lines.extend(new_meta_lines)
    new_lines.append('#')
    new_lines.extend(updated_post_header)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')


def main():

    # Read arguments from command-line
    parser = argparse.ArgumentParser(description="Update metadata master file with new run information.")
    parser.add_argument('--new_meta', required=True, help='Path to new metadata file.')
    parser.add_argument('--master_meta', required=True, help='Path to master metadata file.')
    parser.add_argument('--run_id', required=True, help='Current sequencing run ID')
    parser.add_argument('--output', required=True, help='Path to write updated master metadata')

    args = parser.parse_args()

    try:
        print(f"; Reading new metadata file")
        new_lines = process_new_meta(args.new_meta, args.run_id)
        print(f"; Updating metadata table")
        update_meta_master(args.master_meta, new_lines, args.output)
        print(f"; Metadata updated successfully. Output written to: {args.output}")
    except Exception as e:
        print(f" Error: {e}")


if __name__ == '__main__':
    main()

