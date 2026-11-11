import argparse
import re

from copy import copy, deepcopy
from enum import Flag, auto
from inkscapeprocess import InkscapeProcess
from xml.dom.minidom import Document, Element, Text, parse
from pathlib import Path
from typing import Callable


TemplateFunction = Callable[..., "NodeSet"]


class Style(Flag):
    NONE = 0
    BOLD = auto()
    ITALIC = auto()


class Card:
    def __init__(
        self,
        row_data: dict[str, str],
        card_template: Document,
        inkproc: InkscapeProcess,
        node_class: type["NodeSet"],
    ) -> None:
        self.data = row_data
        self.doc = card_template
        self.proc = inkproc
        # Pass the NodeSet class to Card, or if you want to subclass
        # NodeSet to add more template_funcs or similar, then pass the
        # subclass ("UserNodeSet" or something like that) instead.
        self.node_class = node_class
        self.do()

    def do(self) -> None:
        text_nodes = NodeSet(set(self.doc.getElementsByTagName("text")))
        text_nodes.set_text("qwerty *qwerty* _qwer_ty _*qwer*_ty qwerty qwerty qwerty")


TEMPLATE_BRACKETS_RE = re.compile(r"(?<!\\){([^{]*?)(?<!\\)}")


def bracket_handler(m: re.Match) -> str:
    contents = m.group(1)
    return contents


class NodeSet:
    def __init__(
        self,
        nodes: set[Element] | Element,
        text_templates: Callable[[re.Match], str] = bracket_handler,
    ):
        if isinstance(nodes, Element):
            self.nodes = {nodes}
        else:
            self.nodes = nodes
        self.bracket_handler = bracket_handler

    # Chain template_func method calls together. Each returns a new
    # NodeSet object, with a set of XML nodes to be affected by
    # the next method call.
    def get_classed(self, class_tag: str) -> "NodeSet":
        new_set = set()
        for node in self.nodes:
            for sn in node.getElementsByTagName("*"):
                if class_tag in sn.getAttribute("class").split():
                    new_set.add(sn)
        return NodeSet(new_set)

    def filter(self, class_tag: str) -> "NodeSet":
        new_set = set()
        for node in self.nodes:
            if class_tag in node.getAttribute("class").split():
                new_set.add(node)
        return NodeSet(new_set)

    def elements(self, element_tag: str) -> "NodeSet":
        new_set = set()
        for node in self.nodes:
            for sn in node.getElementsByTagName(element_tag):
                new_set.add(sn)
        return NodeSet(new_set)

    def set_text(self, text: str) -> "NodeSet":
        new_set = set()
        # get styles
        for node in self.nodes:
            if node.tagName != "text":
                continue

            bold, italic, bold_italic = get_styles(node)

            # remove filler text from original
            for rm_n in copy(node.childNodes):
                node.removeChild(rm_n)

            # Handle {} templates:
            text = TEMPLATE_BRACKETS_RE.sub(self.bracket_handler, text)

            # Parse text for light markup
            spans: list[tuple[Style, str]] = parse_markup(text)

            # Add new tspan and content nodes
            add_tspans(node, spans, bold, italic, bold_italic)

            # Change the node's style so that text wraps?

            # Return node because we did stuff to it
            new_set.add(node)
        return NodeSet(new_set)


def get_styles(node: Element) -> tuple[str, str, str]:
    bold = None
    italic = None
    bold_italic = None
    for tspan in node.childNodes:
        if bold and italic and bold_italic:
            break
        if not isinstance(tspan, Element):
            continue
        if tspan.tagName != "tspan":
            continue
        style = tspan.getAttribute("style")
        if not bold and "bold" in style and "italic" not in style:
            bold = style
            continue
        if not italic and "italic" in style and "bold" not in style:
            italic = style
            continue
        if not bold_italic and "italic" in style and "bold" in style:
            bold_italic = style
    if not bold:
        bold = "font-weight:bold;font-style:normal;"
    if not italic:
        italic = "font-style:italic;font-weight:normal;"
    if not bold_italic:
        bold_italic = "font-style:italic;font-weight:bold;"

    return bold, italic, bold_italic


FORMATTING_CHARS_RE = re.compile(r"(\\.|\\$|\*|_)")


def parse_markup(text: str) -> list[tuple[Style, str]]:
    ret: list[tuple[Style, str]] = []
    state = Style.NONE
    prev_state = state

    current: list[str] = []

    for s in FORMATTING_CHARS_RE.split(text):
        # No need to modulo, because the splitters are all static and known
        if not s:
            continue
        elif s.startswith("\\"):
            if len(s) >= 2:
                current.append(s[1:])
        elif s == "*":
            state ^= Style.BOLD
        elif s == "_":
            state ^= Style.ITALIC
        else:
            current.append(s)

        if prev_state != state:
            if len(current) > 0:
                ret.append((prev_state, "".join(current)))
            current.clear()
            prev_state = state

    if len(current) > 0:
        ret.append((state, "".join(current)))

    return ret


def add_tspans(
    node: Element,
    spans: list[tuple[Style, str]],
    bold: str,
    italic: str,
    bold_italic: str,
) -> None:
    # No recursion, all flat tspans
    for style, text in spans:
        t = Text()
        t.data = text
        # If Style is NONE, add a xml.dom.minidom.Text node directly.
        if style == Style.NONE:
            node.appendChild(t)
            continue
        # Otherwise, add a tspan node with a style, and add a Text to that
        tspan = Element("tspan")
        tspan.appendChild(t)
        styleattr = node.ownerDocument.createAttribute("style")
        if style == Style.BOLD:
            styleattr.value = bold
        elif style == Style.ITALIC:
            styleattr.value = italic
        elif style == Style.BOLD | Style.ITALIC:
            styleattr.value = bold_italic
        tspan.setAttributeNode(styleattr)
        node.appendChild(tspan)

    return None


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    # print(type(args.file), args.file)
    f = open(args.file)
    template = parse(f)
    f.close()
    a = Card(dict(), deepcopy(template), None, NodeSet)

    print(a.doc.toxml())
    # print(parse_markup(r"nnnn*bbbbb*nn\*nnn_ii\\i\ii_nnn_ii*bibi*_" + "\\"))
