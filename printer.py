# Take a supplied page layout template and insert
# images into `image` elements to replace placeholders.
# Then output page as pdf.

import argparse
import tempfile

from inkscapeprocess import InkscapeProcess
from copy import deepcopy
from pathlib import Path
from xml.dom import minidom


class CardPrinter:
    def __init__(
        self,
        template_source: Path,
        imgdir: Path,
        outdir: Path,
        inkscape: InkscapeProcess,
    ) -> None:
        card_paths: list[Path] = sorted(
            f for f in imgdir.iterdir() if f.suffix == ".png"
        )
        print("PRINTER -----------")
        print(f"{card_paths=}")

        # Load page template SVG file as XML

        with template_source.open() as f:
            template_root = minidom.parse(f)

        image_frames = list(template_root.getElementsByTagName("image"))
        page_capacity = len(image_frames)
        print(f"{image_frames=}")
        print(f"{page_capacity=}")
        page_nodes: list = []

        for i in range(0, len(card_paths), page_capacity):
            cur_doc = deepcopy(template_root)
            image_frames = list(cur_doc.getElementsByTagName("image"))
            card_batch = card_paths[i : i + page_capacity]
            for i, card_path in enumerate(card_batch):
                frame = image_frames[i]
                frame.setAttribute("xlink:href", str(card_path.absolute()))

            if len(card_batch) < page_capacity:
                for frame in image_frames[len(card_batch) :]:
                    frame.parentNode.removeChild(frame)

            page_nodes.append(cur_doc)

        with tempfile.TemporaryDirectory() as d_string:
            d = Path(d_string)
            padding = len(str(len(page_nodes)))
            for i, page in enumerate(page_nodes):
                fnum = str(i + 1).rjust(padding, "0")
                page_path = d / f"{fnum}.svg"
                with page_path.open("w") as f:
                    page.writexml(f)

            for i, page in enumerate(d.iterdir()):
                if page.suffix != ".svg":
                    continue
                fnum = str(i + 1).rjust(padding, "0")
                page_path = outdir / f"{fnum}.pdf"
                inkscape.load(page)
                inkscape.export_page(page_path)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", type=Path)
    argparser.add_argument("-d", type=Path)
    argparser.add_argument("-o", type=Path)
    args = argparser.parse_args()
    template = args.p
    if not template.is_file() and template.suffix == ".svg":
        print("Template should be .svg file")
        exit(1)
    imgdir = args.d
    if not imgdir.is_dir():
        print("Image directory -d should be directory")
        exit(1)

    outdir = args.o
    if not outdir.exists():
        outdir.mkdir()
    if not outdir.is_dir():
        print("Output directory -o should be directory")
        exit(1)

    inkproc = InkscapeProcess(template)
    printer = CardPrinter(template, imgdir, outdir, inkproc)
