import argparse

from inkscapeprocess import InkscapeProcess
from xml.dom.minidom import Node
from pathlib import Path
from typing import Callable


TemplateFunction = Callable[..., "NodeSet"]


def register_in(register: dict[str, TemplateFunction]) -> TemplateFunction:
    print(f"Reached: {register=}")

    def _register_in(func: TemplateFunction):
        register[func.__name__] = func
        return func
    return _register_in


class Card:
    def __init__(
        self,
        row_data: dict[str, str],
        card_template: Node,
        inkproc: InkscapeProcess,
        node_class: type["NodeSet"],
    ) -> None:
        self.data = row_data
        self.template = card_template
        self.proc = inkproc
        # Pass the NodeSet class to Card here, or if you want to subclass
        # NodeSet to add more template_funcs or similar, then pass the
        # subclass ("UserNodeSet" or something like that) instead.
        self.node_class = node_class


class NodeSet:
    template_funcs: dict[str, TemplateFunction] = {}

    def __init__(self, nodes: set[Node]):
        self.nodes = nodes
        self.funcs = NodeSet.template_funcs

    # Chain template_func method calls together. Each returns a new
    # NodeSet object, with a set of XML nodes to be affected by
    # the next method call.
    @register_in(template_funcs)
    def test(self) -> "NodeSet":
        print("TEST")
        return NodeSet(set())


if __name__ == "__main__":
    # argparser = argparse.ArgumentParser()
    # argparser.add_argument("file", type=Path)
    # args = argparser.parse_args()
    # print(type(args.file), args.file)
    a = Card(dict(), None, None)
    print(a.funcs)
    print(Card.template_funcs)

