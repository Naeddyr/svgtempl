import argparse
import zipfile
from xml.etree import ElementTree as ET
from pathlib import Path

namespaces: dict[str, str] = {
    "presentation": "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0",
    "css3t": "http://www.w3.org/TR/css3-text/",
    "grddl": "http://www.w3.org/2003/g/data-view#",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "formx": "urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "rpt": "http://openoffice.org/2005/report",
    "dc": "http://purl.org/dc/elements/1.1/",
    "chart": "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "oooc": "http://openoffice.org/2004/calc",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "ooow": "http://openoffice.org/2004/writer",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "ooo": "http://openoffice.org/2004/office",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "dr3d": "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "number": "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    "of": "urn:oasis:names:tc:opendocument:xmlns:of:1.2",
    "calcext": "urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0",
    "tableooo": "http://openoffice.org/2009/table",
    "drawooo": "http://openoffice.org/2010/draw",
    "loext": "urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0",
    "dom": "http://www.w3.org/2001/xml-events",
    "field": "urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "math": "http://www.w3.org/1998/Math/MathML",
    "form": "urn:oasis:names:tc:opendocument:xmlns:form:1.0",
    "script": "urn:oasis:names:tc:opendocument:xmlns:script:1.0",
    "xforms": "http://www.w3.org/2002/xforms",
}

for ns in namespaces:
    ET.register_namespace(ns, namespaces[ns])


class Spreadsheet:
    def __init__(self, spreadsheetfile) -> None:
        # rows: list[dict[str, str]] = []
        with open(spreadsheetfile, "r") as ods:
            with zipfile.ZipFile(spreadsheetfile).open(
                "content.xml"
            ) as content:
                xtext = str(content.read(), "utf-8")
                root = ET.fromstring(xtext)
                print(root)
                ET.indent(root)
                print(ET.tostring(root, encoding="unicode"))
                # Extract all the rows and text elements
        # self.titles = rows[0]
        # self.rows = [{k: v for k, v in zip(self.titles, row)} for row in rows]


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = Spreadsheet(args.file)
