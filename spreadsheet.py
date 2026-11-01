import argparse
import zipfile
from xml.dom import minidom
from xml.dom import Node
from pathlib import Path
from typing import Literal

TextTupNode = tuple[
    Literal["root", "", "normal", "i", "b", "ib"], list[str, "TextTupNode"]
]


class Spreadsheet:
    def __init__(self, spreadsheetfile) -> None:
        row_list: list[list[str]] = []
        self.styles: dict[str, list[str]] = {}
        with zipfile.ZipFile(spreadsheetfile).open("content.xml") as content:
            root = minidom.parse(content)

            #  get style info for text formatting
            for style in root.getElementsByTagName("style:style"):
                if not style.getAttribute("style:family") == "text":
                    continue
                propses = style.getElementsByTagName("style:text-properties")
                if len(propses) == 0:
                    continue
                props = propses[0]
                tags: list[str] = []
                if props.getAttribute("fo:font-style") == "italic":
                    tags.append("italic")
                if props.getAttribute("fo:font-weight") == "bold":
                    tags.append("bold")
                style_name = style.getAttribute("style:name")
                self.styles[style_name] = tags

            for row in root.getElementsByTagName("table:table-row"):
                cells = []
                for odsc in row.getElementsByTagName("table:table-cell"):
                    c = DataCell(odsc, self)
                    if repeats := odsc.getAttribute(
                        "table:number-columns-repeated"
                    ):
                        cells.extend([c] * int(repeats))
                    else:
                        cells.append(c)
                row_list.append(cells)
        self.titles = (c.data for c in row_list[0])
        self.rows = [
            {k: v for k, v in zip(self.titles, row) if k}
            for row in row_list[1:]
        ]
        self.titles = [x for x in self.titles if x]


class DataCell:
    def __init__(self, odsnode: Node, document: Spreadsheet):
        self.node = odsnode
        self.doc = document
        self.getAttribute = self.node.getAttribute
        self.nodeType = self.node.nodeType
        self.childNodes = self.node.childNodes
        self.tagName = self.node.tagName

    @property
    def text_tree(self) -> TextTupNode:
        if not self.nodeType == self.node.ELEMENT_NODE:
            return ("", [])
        if self.tagName == "table:table-cell":
            ps = self.node.getElementsByTagName("text:p")
            if len(ps) == 0:
                return ("", [])
            return self._get_text_tree_helper(ps[0], "root")
        return ("", [])

    def _get_text_tree_helper(self, node: Node, prefix: str) -> TextTupNode:
        # get text data with formatting.
        ret: list[str, TextTupNode] = []
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                ret.append(child.data)
                continue
            if sn := child.getAttribute("text:style-name"):
                style = self.doc.styles[sn]
                pref = ""
                if "italic" in style:
                    pref = "i"
                if "bold" in style:
                    pref += "b"
                ret.append(self._get_text_tree_helper(child, pref))
            else:
                ret.append(self._get_text_tree_helper(child, "n"))
        return (prefix, ret)

    @property
    def data(self) -> str:
        # get only data, no formatting
        ret: list[str] = []
        for child in self.childNodes:
            if child.nodeType == child.TEXT_NODE:
                ret.append(child.data)
                continue
            ret.append(self._get_data_helper(child))
        return "".join(ret)

    def _get_data_helper(self, node) -> str:
        ret: list[str] = []
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                ret.append(child.data)
                continue
            ret.append(self._get_data_helper(child))
        return "".join(ret)


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
