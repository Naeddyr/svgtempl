import argparse
import actions as act

from .inkscapeprocess import InkscapeProcess
from pathlib import Path

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = InkscapeProcess(args.file)
