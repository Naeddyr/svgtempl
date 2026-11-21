import math
import re
import tempfile

from contextlib import contextmanager
from copy import copy
from enum import Flag, auto
from svgtempl.actions import Act
from svgtempl.inkscapeprocess import InkscapeProcess
from svgtempl.spreadsheet import DataCell
from svgtempl.types import Point, Matrix, Transform
from svgtempl.units import Unit
from xml.dom.minidom import Document, Element, Text, parse, parseString
from typing import Callable, Generator, Literal


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
        card_template: str,
        inkproc: InkscapeProcess,
        user_script: Callable[["Card"], None],
        node_type: type["NodeSet"] | None = None,
        text_templater: Callable[[re.Match], str] | None = None,
        copies: int = 1,
    ) -> None:
        self.data = row_data
        # Earlier had trouble with deepcopy in another part of the code;
        # for some reason it seemed like the deepcopied DOM had some sort sort
        # of infinite cycle. We'll address this by just getting new copies
        # by reparsing.
        self.doc = parseString(card_template)
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

        # Element ids that are marked to be removed at the end of the process.
        self.tb_removed: list[str] = []

        self.measurement_units: Unit = self.get_measurement_units()
        self.proc.units = self.measurement_units

    def generate(self) -> Document:
        # Run user-provided script
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".svg") as f:
            # self.inkfile is the temporary file used to communicate with
            # the Inkscape process
            self.inkfile = f
            self.user_script(self)

        # Remove marked elements as a cleanup step at the very end.
        # It's less likely that something goes wrong when you have stuff
        # that is marked for deletion, compared with deleting it when
        # all sorts of things are flying around. Maybe...
        self.root.find_ids(self.tb_removed)._remove()
        return self.doc

    @property
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

    def get_measurement_units(self) -> Unit:
        root = self.doc.documentElement
        assert root is not None
        ret = Unit.PX
        for x in ("width", "height"):
            s = root.getAttribute(x)[-2:]
            # Python 3.10 hack to check if a value is found in an enum
            # Python 3.12 has this as just `s in Unit`.
            if s in Unit._value2member_map_:
                ret = Unit(s)
                break
        return ret


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

        # just a quick alias
        self.action = self.card.proc.action

    def id_list(self) -> list[str]:
        ret = []
        for node in self.nodes:
            ret.append(node.getAttribute("id"))
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

    def remove(self) -> "NodeSet":
        self.card.tb_removed.extend(self.id_list())
        return self

    def _remove(self) -> None:
        for node in self.nodes:
            if par := node.parentNode:
                par.removeChild(node)

    def set_attrib(self, attribs: dict[str, str]) -> "NodeSet":
        for node in self.nodes:
            for k, v in attribs.items():
                node.setAttribute(k, v)
        return self

    def update_inkscape(self) -> None:
        self.card.doc.writexml(self.card.inkfile)
        self.card.proc.load(self.card.inkfile.name)

    def from_inkscape(self) -> None:
        self.action(
            (
                (
                    Act.EXPORT_NAME,
                    str(self.card.inkfile),
                ),
                (Act.EXPORT_TYPE, "svg"),
                (Act.EXPORT_DO,),
            )
        )
        self.doc = parse(self.card.inkfile)

    @contextmanager
    def inkscape(
        self,
    ) -> Generator[tuple[InkscapeProcess, Document], None, None]:
        # Because we don't want there to be two "document trees" that are
        # modified at the same time, a contextmanager and `with` blocks
        # should make it easier.
        self.card.doc.writexml(self.card.inkfile)

        # We break self.card.doc on purpose so that users will not modify
        # a document that will be replaced by the export from Inkscape
        # when closing the context
        # HOWEVER, if there is a need to read the old data while inside
        # inkscape context, we can provide the old reference as an explicit
        # "deprecated" tree
        old_doc = self.card.doc
        # This should break typecheckers, too. This is a program to do
        # some svg image templating, we can just panic.
        self.card.doc = None

        self.card.proc.load(self.card.inkfile.name)

        try:
            # yield only once to contexmanager. this is all from example docs
            # should really use more try blocks but...
            yield self.card.proc, old_doc

        # Stuff that should happen when contextmanager releases the yield
        # by `yielding` again... at least I think that's how it works.
        finally:
            self.action(
                (
                    (
                        Act.EXPORT_NAME,
                        str(self.card.inkfile),
                    ),
                    (Act.EXPORT_TYPE, "svg"),
                    (Act.EXPORT_DO,),
                )
            )
            self.doc = parse(self.card.inkfile)

    def _simple_transform(
        self,
        action: Literal[Act.ROTATE, Act.TRANSLATE, Act.SCALE],
        args: float | tuple[float, float],
    ) -> "NodeSet":
        ids = self.id_list()

        self.update_inkscape()  # XXX this could be a `with` context thing....

        # make a selection of all the id'd objects
        self.card.proc.action(((Act.SELECT, *ids),))
        # perform the transform actions (so we don't need to do it manually)
        if action == Act.ROTATE:
            assert isinstance(args, float)
            self.action(((action, str(args)),))
        elif action == Act.SCALE:
            assert isinstance(args, float)
            self.action(((action, str(args)),))
        elif action == Act.TRANSLATE:
            assert isinstance(args, tuple)
            assert len(args) == 2
            self.action(((action, str(args[0]), str(args[1])),))

        # finish handling stuff in inkscape and update self.doc
        self.from_inkscape()

        return self.card.root.find_ids(ids)


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


def get_css(node: Element) -> dict[str, str]:
    css = node.getAttribute("style")
    ret = {}
    for pair in css.split(";"):
        k, v = pair.split(":")[0:2]
        ret[k.strip()] = v.strip()
    return ret


def set_css(node: Element, css_in: dict[str, str]) -> None:
    # Replace 'style' with new CSS
    pairs = []
    for k, v in css_in.items():
        pairs.append(f"{k}:{v}")
    node.setAttribute("style", ";".join(pairs))


def update_css(node: Element, css_update: dict[str, str]) -> None:
    # Update 'style' with changes
    css = get_css(node)
    for k, v in css_update.items():
        css[k] = v
    set_css(node, css)


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


TRANSFORM_CALLS_RE = re.compile(r"(\w+)\(([^)]*)\)")


def get_transforms(node: Element) -> Transform:
    #     // calculate delta transform point
    #     var px = deltaTransformPoint(matrix, { x: 0, y: 1 });
    #     var py = deltaTransformPoint(matrix, { x: 1, y: 0 });
    tr_field = node.getAttribute("transform").strip()

    if not tr_field:
        return Transform(0, 0, 0, 0, 0, 0, 0)

    for m in TRANSFORM_CALLS_RE.findall(tr_field):
        call = m.group(1).strip().lowercase()
        params = m.group(2).strip()
        if call == "matrix":
            vals = re.split(r"\s*,\s*|\s*", params)
            matrix_res = Matrix(*(float(s) for s in vals))
        elif call == "":
            ...
        ...

    return Transform(*(map(sum, zip(matrix_res, ...))))


def deltatransform_point(m: Matrix, p: Point) -> Point:
    dx = p.x * m.a + p.y * m.c
    dy = p.x * m.b + p.y * m.d
    return Point(dx, dy)


def decompose_matrix(m: Matrix) -> Transform:
    px = deltatransform_point(..., Point(0, 1))
    py = deltatransform_point(..., Point(1, 0))

    skewx = (180 / math.pi) * math.atan2(px.y, px.x) - 90
    #     // calculate skew
    #     var skewX = ((180 / Math.PI) * Math.atan2(px.y, px.x) - 90);
    #     var skewY = ((180 / Math.PI) * Math.atan2(py.y, py.x));

    #     return {

    #         translateX: matrix.e,
    #         translateY: matrix.f,
    #         scaleX: Math.sqrt(matrix.a * matrix.a + matrix.b * matrix.b),
    #         scaleY: Math.sqrt(matrix.c * matrix.c + matrix.d * matrix.d),
    #         skewX: skewX,
    #         skewY: skewY,
    #         rotation: skewX // rotation is the same as skew x
    #     };
    # }
    return Transform(0, 0, 0, 0, 0, 0, 0)
