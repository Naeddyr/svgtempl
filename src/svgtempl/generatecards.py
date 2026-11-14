import argparse

from inkscapeprocess import InkscapeProcess
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
    run_parser.set_defaults(func=run)
    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=init)
    args = argparser.parse_args()
    return args.func(args)


def run(args) -> int:
    print(args)
    print("RUN")
    template = args.template
    if not template.is_file() and template.suffix == ".svg":
        print("Template should be .svg file")
        return 1
    data = args.data
    if not data.is_file():
        return 2

    outdir = args.outdir
    if not outdir.exists():
        outdir.mkdir()
    if not outdir.is_dir():
        print("Output directory -o should be directory")
        return 1

    inkproc = InkscapeProcess(template)
    # printer = CardPrinter(template, imgdir, outdir, inkproc)

    return 0


def init(args) -> int:
    print(args)
    print("INIT")
    return 0


if __name__ == "__main__":
    exit(main())
