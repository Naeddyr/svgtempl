import re

from copy import copy
from svgtempl.actions import Act

from svgtempl.svg import get_rotation
from svgtempl.xml import get_id, get_styles, add_tspans
from svgtempl.text import parse_markup, Style
from xml.dom.minidom import Element
from typing import Callable, Literal, ParamSpec, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from svgtempl.card import Card


T = TypeVar("T")
P = ParamSpec("P")
TEMPLATE_BRACKETS_RE = re.compile(r"(?<!\\){([^{]*?)(?<!\\)}")


def inkscape_lock(f: Callable[P, T]) -> Callable[P, T]:
    """Prevent users and other code from manipulating Selections when
    Inkscape is doing changes at the same time."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        # This seems really hard or impossible to annotate sensibly
        # args[0] should always be "self"
        if args[0].card._lock is True:  # type: ignore
            raise Exception(
                f"Inkscape context: do not run `{f.__name__}()` "
                "inside an Inkscape context block because its "
                "result will be overridden when Inkscape finishes."
            )
        return f(*args, **kwargs)

    return wrapper


class Selection:
    card: "Card"
    store: dict[str, tuple[str, ...]] = {}

    def __init__(
        self,
        nodes: list[Element] | tuple[Element] | Element,
    ):
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        else:
            nodes = nodes

        new_nodes = []
        for x in nodes:
            if x not in new_nodes:
                new_nodes.append(x)

        self.nodes: tuple[Element, ...] = tuple(new_nodes)

    def id_list(self) -> tuple[str, ...]:
        ret = []
        for node in self.nodes:
            ret.append(node.getAttribute("id"))
        return tuple(ret)

    def store_as(self, key: str) -> "Selection":
        # Convenience func to save ids if you don't want to interrupt a
        # function class chain
        self.store[key] = self.id_list()
        return self

    @inkscape_lock
    def update(self) -> "Selection":
        ids = self.id_list()
        root = self.card.doc.documentElement
        assert root is not None
        self.nodes = (root,)
        return self.find_ids(ids)

    # Chain template_func method calls together. Each returns a new
    # Selection object, with a set of XML nodes to be affected by
    # the next method call.

    def find_ids(self, ids: list[str] | tuple[str, ...]) -> "Selection":
        new_set = []
        for node in self.nodes:
            for sn in node.getElementsByTagName("*"):
                if sn.getAttribute("id") in ids:
                    new_set.append(sn)
        return type(self)(new_set)

    def find_class(self, class_tag: str | list[str]) -> "Selection":
        new_set = []
        if isinstance(class_tag, str):
            for node in self.nodes:
                for sn in node.getElementsByTagName("*"):
                    if class_tag in sn.getAttribute("class").split():
                        new_set.append(sn)
            return type(self)(new_set)
        else:
            for node in self.nodes:
                for sn in node.getElementsByTagName("*"):
                    for snclass in sn.getAttribute("class").split():
                        if snclass in class_tag:
                            new_set.append(sn)
                            break
            return type(self)(new_set)

    find_classes = find_class

    def filter_class(self, class_tag: str) -> "Selection":
        new_set = []
        for node in self.nodes:
            if class_tag in node.getAttribute("class").split():
                new_set.append(node)
        return type(self)(new_set)

    def find_elements(self, element_tag: str) -> "Selection":
        new_set = []
        for node in self.nodes:
            for sn in node.getElementsByTagName(element_tag):
                new_set.append(sn)
        return type(self)(new_set)

    def filter_element(self, element_tag: str) -> "Selection":
        new_set = []
        for node in self.nodes:
            if node.tagName == element_tag:
                new_set.append(node)
        return type(self)(new_set)

    @inkscape_lock
    def set_text(self, text: str) -> "Selection":
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
        return type(self)(new_set)

    @inkscape_lock
    def remove(self) -> "Selection":
        self.card.tb_removed.extend(self.id_list())
        return self

    def _remove(self) -> None:
        for node in self.nodes:
            if par := node.parentNode:
                par.removeChild(node)

    @inkscape_lock
    def set_attrib(
        self, attribs: dict[str, str | Callable[[str], str]]
    ) -> "Selection":
        """Set attributes of an element using a dict that replaces values.
        Instead of a value, you may provide a function that reads the original
        value and returns a string based on it."""
        for node in self.nodes:
            for k, v in attribs.items():
                if not isinstance(v, str):  # how do you check for a function
                    node.setAttribute(k, v(node.getAttribute(k)))
                else:
                    node.setAttribute(k, v)
        return self

    @inkscape_lock
    def _simple_transform(
        self,
        action: Literal[Act.ROTATE, Act.TRANSLATE, Act.SCALE],
        args: float | tuple[float, float],
    ) -> "Selection":
        ids = self.id_list()

        with self.card.inkscape() as inkscape:
            # make a selection of all the id'd objects
            inkscape.action(Act.ADD, *ids)
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
            inkscape.clear()

        return self.card.root.find_ids(ids)

    @inkscape_lock
    def add_icons(self, icon_id: str) -> "Selection":
        icon = self.card.root.find_ids([icon_id])
        assert len(icon.nodes) == 1, (
            f"There should be exactly 1 element with an id "
            f"{icon_id=}, but found {len(icon.nodes)}"
        )
        icon_el = icon.nodes[0]
        self.card.make_definition(icon_el)

        anchor_pairs: list[tuple[str, str, float]] = []
        for node in self.nodes:
            origin_id = get_id(node)
            rotation = get_rotation(node)
            id, use_node = self.card.create_clone(origin_id)
            self.card.anchors[id] = origin_id
            anchor_pairs.append((id, origin_id, rotation))

        with self.card.inkscape() as ink:
            for id, origin, rot in anchor_pairs:
                ink.align(id, origin)
                ink.rotate(id, rot)

        return self
