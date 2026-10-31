import argparse
import zipfile
from xml.dom import minidom
from xml.dom import Node
from pathlib import Path
from typing import Generator


class Spreadsheet:
    def __init__(self, spreadsheetfile) -> None:
        # rows: list[dict[str, str]] = []
        row_list: list[list[str]] = []
        with zipfile.ZipFile(spreadsheetfile).open("content.xml") as content:
            root = minidom.parse(content)
            for row in root.getElementsByTagName("table:table-row"):
                cells = []
                for c in row.getElementsByTagName("table:table-cell"):
                    txt = "".join(get_text(c))
                    if repeats := c.getAttribute("table:number-columns-repeated"):
                        cells.extend([txt] * int(repeats))
                    else:
                        cells.append(txt)
                row_list.append(cells)
        self.titles = row_list[0]
        self.rows = [
            {k: v for k, v in zip(self.titles, row) if k}
            for row in row_list[1:]
        ]
        self.titles = [x for x in self.titles if x]

def get_text(node: Node) -> Generator[str, None, None]:
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            yield child.data
            continue
        yield from get_text(child)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = Spreadsheet(args.file)
    print("First row (skipping empty cells)", sheet.titles)
    print("Following rows: ", sheet.rows)
