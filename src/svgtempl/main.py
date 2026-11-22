import argparse
import importlib
import sys
import tempfile

from svgtempl.card import Card
from svgtempl.inkscapeprocess import InkscapeProcess
from svgtempl.printer import print_cards
from svgtempl.spreadsheet import Spreadsheet
from pathlib import Path
from shutil import which


def main() -> int:
    if which("inkscape") is None:
        print(
            "It seems this script has no access to an `inkscape` command; "
            "please install Inkscape."
        )
        return 1
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers()

    # svgtempl run
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--template", "-t", type=Path)
    run_parser.add_argument("--outdir", "-o", type=Path)
    run_parser.add_argument("--data", "-d", type=Path)
    run_parser.add_argument("--page-template", "-p", type=Path)
    run_parser.add_argument("--script", "-s", type=Path)
    run_parser.add_argument("--export-cards", "-c", action="store_true")
    run_parser.set_defaults(func=run)

    # svgtempl init
    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=init)
    # Generate:
    #   Card svg template file
    #   Page svg template file
    #     A4 or Letter toggle
    #   Card generator script user file
    #   Separate Selection subclassing file?
    #   Spreadsheet template
    #     Toggle ODS or CSV
    args = argparser.parse_args()
    return args.func(args)


def run(args) -> int:
    print(args)
    print("RUN")
    template = args.template
    if template is None:
        template = Path("template.svg")
    if not (template.is_file() and template.suffix == ".svg"):
        print("Please provide an SVG file as your card template")
        return 1
    with open(template) as f:
        card_template = f.read()
    # WIP: enable the use of several different templates that can be switched
    # between as needed.

    data = args.data
    if data is None:
        for p in ("data.ods",):  # "data.csv", excel?
            try_path = Path(p)
            if try_path.is_file():
                data = try_path
                break
    print(data)
    if not (data.is_file() and data.suffix in (".ods",)):
        print("Data should be an .ods spreadsheet file")
        return 1

    outdir = args.outdir
    if outdir is None:
        outdir = Path("out/")
    if not outdir.exists():
        outdir.mkdir()
    if not outdir.is_dir():
        print("Output directory -o should be directory")
        return 1

    page_template = args.page_template
    if page_template is None:
        page_template = Path("page_template.svg")
        for p in ("page-template.svg", "page_template.svg"):
            try_path = Path(p)
            if try_path.is_file():
                page_template = try_path
                break
    if not (page_template.is_file() and page_template.suffix == ".svg"):
        print("Page template for printing should be .svg file")
        return 1

    script = args.script
    if script is None:
        script = Path("script.py")
    if not (script.is_file() and script.suffix == ".py"):
        print(
            "Please provide a generation script (generate boilerplate with "
            "the command `svgtempl init` in a project folder)"
        )
        return 1

    user_script = import_from_path("user_script", str(script))

    inkproc = InkscapeProcess(template)
    spreadsheet_data = Spreadsheet(data)
    print(f"{inkproc=}, {spreadsheet_data.rows=}")
    with tempfile.TemporaryDirectory() as d_string:
        card_cache = Path(d_string)
        print(card_cache)
        cards = []
        for i, row in enumerate(spreadsheet_data.rows):
            card = Card(row, card_template, inkproc, user_script.user_script)
            card.generate()
            cards.append(card)

        padding = len(str(len(cards)))
        print_amounts: dict[Path, int] = {}
        for i, card in enumerate(cards):
            fnum = str(i + 1).rjust(padding, "0")
            card_path = card_cache / f"{fnum}.svg"
            if args.export_cards is True:
                png_path = outdir / f"{fnum}.png"
            else:
                png_path = card_cache / f"{fnum}.png"
            print_amounts[png_path] = card.copies
            with card_path.open("w") as f:
                card.doc.writexml(f)
            inkproc.load(card_path)
            inkproc.export_page(png_path)

        print(f"{print_amounts=}")
        if args.export_cards is not True:
            print_cards(
                page_template, card_cache, outdir, inkproc, print_amounts
            )

    return 0


def init(args) -> int:
    print(args)

    # Generate new files; script with boilerplate, template svg file,
    # page template svg, data spreadsheet file
    print("INIT TEST")
    return 0


if __name__ == "__main__":
    exit(main())


def import_from_path(module_name: str, file_path: str):
    # taken straight from https://docs.python.org/3/library/importlib.html
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
