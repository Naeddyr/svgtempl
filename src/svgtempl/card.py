import argparse
import re

from copy import copy, deepcopy
from enum import Flag, auto
from svgtempl.inkscapeprocess import InkscapeProcess
from svgtempl.spreadsheet import DataCell
from xml.dom.minidom import Document, Element, Text, parse
from pathlib import Path
from typing import Callable


TemplateFunction = Callable[..., "NodeSet"]


class Style(Flag):
    NONE = 0
    BOLD = auto()
    ITALIC = auto()


ID_RE = re.compile(r"(.*svgtempl_)\d+")


class Card:
    def __init__(
        self,
        row_data: dict[str, DataCell],
        card_template: Document,
        inkproc: InkscapeProcess,
        user_script: Callable[["Card"], None],
        node_type: type["NodeSet"] | None = None,
        text_templater: Callable[[re.Match], str] | None = None,
        copies: int = 1,
    ) -> None:
        self.data = row_data
        self.doc = deepcopy(card_template)
        self.proc = inkproc
        self.user_script = user_script
        # Pass the NodeSet class to Card, or if you want to subclass
        # NodeSet to add more template_funcs or similar, then pass the
        # subclass ("UserNodeSet" or something like that) instead.
        self.node_type = node_type
        if text_templater is not None:
            self.bracket_handler = text_templater
        else:
            self.bracket_handler = default_bracket_handler
        self.cur_id = 0
        # How many times to duplicate this card when printing
        # If this information is in the spreadsheet, modify this inside self
        self.copies = copies

        # Meta-dicts for different element relationships. Keys and values
        # should be element ids. Because we may load the SVG document into
        # inkscape and then retrieve the data after inkscape modifies it, we
        # need to reload everything and each element is recreated and becomes
        # anonymous, except for the `id` field

        # Element copied or derived from another, because the original already
        # has an id
        # New element -> original
        self.originals: dict[str, str] = {}

        # Element created with reference to an anchor element:
        # New element -> anchor
        self.anchors: dict[str, str] = {}

    def generate(self) -> Document:
        self.user_script(self)

        return self.doc


    def root(self) -> "NodeSet":
        root = self.doc.documentElement
        assert root is not None
        return NodeSet(self, root)

    def new_id(self, orig: str | None = None) -> str:
        if orig is None:
            id = f"svgtempl_{self.cur_id}"
        elif m := ID_RE.match(orig):
            id = f"{m.group(1)}{self.cur_id}"
        else:
            id = f"{orig}_svgtempl_{self.cur_id}"

        # Map new element -> original
        if orig is not None:
            self.originals[id] = orig

        self.cur_id += 1
        return id


TEMPLATE_BRACKETS_RE = re.compile(r"(?<!\\){([^{]*?)(?<!\\)}")


def default_bracket_handler(m: re.Match) -> str:
    contents = m.group(1)
    # WIP
    return contents


class NodeSet:
    def __init__(
        self,
        card: Card,
        nodes: list[Element] | Element,
    ):
        self.card = card
        if not isinstance(nodes, list):
            self.nodes = [nodes]
        else:
            self.nodes = nodes

    def id_list(self) -> list[str]:
        ret = []
        for node in self.nodes:
            for id in node.getAttribute("id"):
                ret.append(id)
        return ret

    def update(self) -> "NodeSet":
        ids = self.id_list()
        root = self.card.doc.documentElement
        assert root is not None
        self.nodes = [root]
        return self.find_ids(ids)

    # Chain template_func method calls together. Each returns a new
    # NodeSet object, with a set of XML nodes to be affected by
    # the next method call.

    def find_ids(self, ids: list[str]) -> "NodeSet":
        new_set = []
        for node in self.nodes:
            for sn in node.getElementsByTagName("*"):
                if sn.getAttribute("id") in ids:
                    new_set.append(sn)
        return NodeSet(self.card, new_set)

    def find_class(self, class_tag: str | list[str]) -> "NodeSet":
        new_set = []
        if isinstance(class_tag, str):
            for node in self.nodes:
                for sn in node.getElementsByTagName("*"):
                    if class_tag in sn.getAttribute("class").split():
                        new_set.append(sn)
            return NodeSet(self.card, new_set)
        else:
            for node in self.nodes:
                for sn in node.getElementsByTagName("*"):
                    for snclass in sn.getAttribute("class").split():
                        if snclass in class_tag:
                            new_set.append(sn)
                            break
            return NodeSet(self.card, new_set)

    find_classes = find_class

    def filter_class(self, class_tag: str) -> "NodeSet":
        new_set = []
        for node in self.nodes:
            if class_tag in node.getAttribute("class").split():
                new_set.append(node)
        return NodeSet(self.card, new_set)

    def find_elements(self, element_tag: str) -> "NodeSet":
        new_set = []
        for node in self.nodes:
            for sn in node.getElementsByTagName(element_tag):
                new_set.append(sn)
        return NodeSet(self.card, new_set)

    def filter_element(self, element_tag: str) -> "NodeSet":
        new_set = []
        for node in self.nodes:
            if node.tagName == element_tag:
                new_set.append(node)
        return NodeSet(self.card, new_set)

    def set_text(self, text: str) -> "NodeSet":
        new_set = []
        # get styles
        for node in self.nodes:
            if node.tagName != "text":
                continue

            bold, italic, bold_italic = get_styles(node)

            # remove filler text from original
            for rm_n in copy(node.childNodes):
                node.removeChild(rm_n)

            # Handle {} templates:
            text = TEMPLATE_BRACKETS_RE.sub(self.card.bracket_handler, text)

            # Parse text for light markup
            spans: list[tuple[Style, str]] = parse_markup(text)

            # Add new tspan and content nodes
            add_tspans(node, spans, bold, italic, bold_italic)

            # Change the node's style so that text wraps?

            # Return node because we did stuff to it
            new_set.append(node)
        return NodeSet(self.card, new_set)


def nearest_classed(node: Element, target_class: str) -> Element | None:
    # Get nearest element with class x above this node in the document
    # (xml closest)
    cur: Element | None = None
    root = node.ownerDocument
    if root is None:
        return None
    for n in root.getElementsByTagName("*"):
        if target_class in n.getAttribute("class").split():
            cur = n
        if n == node:
            break
    return cur


def get_styles(node: Element) -> tuple[str, str, str]:
    bold = None
    italic = None
    bold_italic = None
    # pick up specific styles already present
    for tspan in node.getElementsByTagName("tspan"):
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
    # defaults
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
    doc = node.ownerDocument
    assert doc is not None
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
        styleattr = doc.createAttribute("style")
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
    a = Card(dict(), template, None, NodeSet, None)

    print(a.doc.toxml())
    # print(parse_markup(r"nnnn*bbbbb*nn\*nnn_ii\\i\ii_nnn_ii*bibi*_" + "\\"))
