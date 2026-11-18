import argparse
import zipfile
from xml.dom import minidom
from xml.dom.minidom import CharacterData, Element, Text
from pathlib import Path


class Spreadsheet:
    def __init__(self, spreadsheetfile) -> None:
        row_list: list[list[DataCell]] = []
        with zipfile.ZipFile(spreadsheetfile).open("content.xml") as content:
            root = minidom.parse(content)

            for i, row in enumerate(
                root.getElementsByTagName("table:table-row")
            ):
                cells = []
                for odsc in row.getElementsByTagName("table:table-cell"):
                    c = DataCell(
                        odsc,
                        self,
                        i + 1,  # Spreadsheet rows are not 0-indexed
                    )
                    if repeats := odsc.getAttribute(
                        "table:number-columns-repeated"
                    ):
                        cells.extend([c] * int(repeats))
                    else:
                        cells.append(c)
                row_list.append(cells)
        self.titles: tuple[str, ...] = tuple(c.data for c in row_list[0])
        # We ignore columns where the first cell (header) is empty
        self.rows: list[dict[str, DataCell]] = [
            {k: v for k, v in zip(self.titles, row) if k}
            for row in row_list[1:]
        ]
        for drow in self.rows:
            for k, v in drow.items():
                v.column = k
        self.titles = tuple(x for x in self.titles if x)


class DataCell:
    def __init__(
        self,
        odsnode: Element | Text | CharacterData,
        document: Spreadsheet,
        row_number: int,
    ):
        self.node = odsnode
        self.doc = document
        self.row_number = row_number
        self.column = ""

    def __str__(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return f"'{self.data}'"

    @property
    def data(self) -> str:
        # get only data, no formatting
        ret: list[str] = []
        for child in self.node.childNodes:
            ret.append(self._get_data_helper(child))
        return "".join(ret)

    def _get_data_helper(self, node) -> str:
        ret: list[str] = []
        if node.nodeType == node.TEXT_NODE:
            return node.data
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                ret.append(child.data)
                continue
            ret.append(self._get_data_helper(child))
        return "".join(ret)

    def get_int(self, default: int = 0) -> int:
        s = self.data
        try:
            return int(s)
        except Exception:
            print(
                f"Could not parse '{s}' in row {self.row_number} column "
                f"{self.column} as an int! Defaulting to {default}"
            )
            return default

    def float(self, default: float = 0.0) -> float:
        try:
            return float(self.data)
        except Exception:
            print(
                print(
                    f"Could not parse '{self.data}' in row "
                    f"{self.row_number} column "
                    f"{self.column} as an int! Defaulting to {default}"
                )
            )
            return default


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = Spreadsheet(args.file)
    print(
        "First row (skipping empty cells)",
        sheet.titles,
    )
    print("Following rows: ", sheet.rows)
    for row in sheet.rows:
        for k, v in row.items():
            print(v.data)
