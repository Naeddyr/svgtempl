import argparse

from .inkscapeprocess import InkscapeProcess
from shutil import which

# from xml.dom.minidom import Document, Element, Text, parse
from pathlib import Path
# from typing import Callable


def main() -> int:
    if which("inkscape") is None:
        print("It seems this script has no access to an `inkscape` command; "
              "please install Inkscape.")
        return 1
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers()
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--template", "-t", type=Path)
    run_parser.add_argument("--outdir", "-o", type=Path)
    run_parser.add_argument("--data", "-d", type=Path)
    run_parser.add_argument("--page-template", "-p", type=Path)
    run_parser.add_argument("--script", "-s", type=Path)
    run_parser.set_defaults(func=run)
    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=init)
    args = argparser.parse_args()
    return args.func(args)


def run(args) -> int:
    print(args)
    print("RUN")
    template = args.template
    if template is None:
        template = Path("template.svg")
    if not template.is_file() and template.suffix == ".svg":
        print("Please provide an SVG file as your card template")
        return 1

    data = args.data
    if data is None:
        # TBD: implement .cvs and Excel? Then try to find one of these three
        # options in the folder
        data = Path("data.ods")
    if not data.is_file() and template.suffix == ".ods":
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
    if not page_template.is_file() and page_template.suffix == ".svg":
        print("Page template for printing should be .svg file")
        return 1

    script = args.script
    if script is None:
        script = Path("script.py")
    if not script.is_file() and script.suffix == ".py":
        print("Please provide a generation script (generate boilerplate with "
              "the command `svgtempl init` in a project folder)")
        return 1

    inkproc = InkscapeProcess(template)
    # printer = CardPrinter(template, imgdir, outdir, inkproc)

    return 0


def init(args) -> int:
    print(args)
    # Generate new files; script with boilerplate, template svg file,
    # page template svg, data spreadsheet file
    print("INIT TEST")
    return 0


if __name__ == "__main__":
    exit(main())
