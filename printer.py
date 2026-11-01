# Take a supplied page layout template and insert
# images into `image` elements to replace placeholders.
# Then output page as pdf.

import argparse

from pathlib import Path

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", type=Path)
    argparser.add_argument("-d", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = Spreadsheet(args.file)
    print(
        "First row (skipping empty cells)",
        sheet.titles,
    )
    print("Following rows: ", sheet.rows)
