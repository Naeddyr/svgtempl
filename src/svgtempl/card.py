import re
import tempfile

from contextlib import contextmanager
from copy import copy
from svgtempl.actions import Act
from svgtempl.inkscapeprocess import InkscapeProcess
from svgtempl.spreadsheet import DataCell
from svgtempl.xml import get_styles, add_tspans
from svgtempl.text import parse_markup, Style
from svgtempl.units import Unit
from xml.dom.minidom import Document, Element, parse, parseString
from typing import Callable, Generator, Literal, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

TemplateFunction = Callable[..., "NodeSet"]


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

        # the lock used to break certain NodeSet methods from running when
        # inside an Inkscape context
        self._lock = False

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

    @contextmanager
    def inkscape(
        self, read_only=False
    ) -> Generator[InkscapeProcess, None, None]:
        # Because we don't want there to be two "document trees" that are
        # modified at the same time, a contextmanager and `with` blocks
        # should make it easier.
        # `read_only` should be set True when you want to only query
        # something from Inkscape, especially when you want to make changes
        # and then check the results.

        self.doc.writexml(self.inkfile)

        if read_only is not True:
            # We break self.card.doc on purpose so that users will not modify
            # a document that will be replaced by the export from Inkscape
            # when closing the context
            # HOWEVER, if there is a need to read the old data while inside
            # inkscape context, we can provide the old reference as an explicit
            # "deprecated" tree
            # This should break typecheckers, too. This is a program to do
            # some svg image templating, we can just panic.
            self._lock = True

        self.proc.load(self.inkfile.name)

        try:
            # yield only once to contexmanager. this is all from example docs
            # should really use more try blocks but...
            yield self.proc

        # Stuff that should happen when contextmanager releases the yield
        # by `yielding` again... at least I think that's how it works.
        finally:
            if read_only is not True:
                self.proc.export_page(self.inkfile.name)
                self.doc = parse(self.inkfile)
                self._lock = False


TEMPLATE_BRACKETS_RE = re.compile(r"(?<!\\){([^{]*?)(?<!\\)}")


def default_bracket_handler(m: re.Match) -> str:
    contents = m.group(1)
    # WIP
    return contents


def inkscape_lock(f: Callable[P, T]) -> Callable[P, T]:
    """Prevent users and other code from manipulating NodeSets when
    Inkscape is doing changes at the same time."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        # This seems really hard or impossible to annotate sensibly
        # args[0] should always be "self"
        if args[0].card._lock is True:  # type: ignore
            raise Exception(
                "Inkscape context: do not run this method, because its "
                "result will be overridden when Inkscape finishes."
            )
        return f(*args, **kwargs)

    return wrapper


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
            ret.append(node.getAttribute("id"))
        return ret

    @inkscape_lock
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

    @inkscape_lock
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

    @inkscape_lock
    def remove(self) -> "NodeSet":
        self.card.tb_removed.extend(self.id_list())
        return self

    def _remove(self) -> None:
        for node in self.nodes:
            if par := node.parentNode:
                par.removeChild(node)

    @inkscape_lock
    def set_attrib(self, attribs: dict[str, str]) -> "NodeSet":
        for node in self.nodes:
            for k, v in attribs.items():
                node.setAttribute(k, v)
        return self

    def _simple_transform(
        self,
        action: Literal[Act.ROTATE, Act.TRANSLATE, Act.SCALE],
        args: float | tuple[float, float],
    ) -> "NodeSet":
        ids = self.id_list()

        with self.card.inkscape() as inkscape:
            # make a selection of all the id'd objects
            inkscape.action(Act.SELECT, *ids)
            # perform the transform actions, so we don't need to do it manually
            if action == Act.ROTATE:
                assert isinstance(args, float)
                inkscape.action(action, str(args))
            elif action == Act.SCALE:
                assert isinstance(args, float)
                inkscape.action(action, str(args))
            elif action == Act.TRANSLATE:
                assert isinstance(args, tuple)
                assert len(args) == 2
                inkscape.action(action, str(args[0]), str(args[1]))

        return self.card.root.find_ids(ids)
