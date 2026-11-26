import re
import tempfile

from contextlib import contextmanager
from svgtempl.inkscapeprocess import InkscapeProcess
from svgtempl.selection import Selection
from svgtempl.spreadsheet import DataCell
from svgtempl.units import Unit
from xml.dom.minidom import Document, parse, parseString
from typing import Callable, Generator

TemplateFunction = Callable[..., "Selection"]


ID_RE = re.compile(r"(.*svgtempl_)\d+")


def default_bracket_handler(m: re.Match) -> str:
    contents = m.group(1)
    # WIP
    return contents


class Card:
    def __init__(
        self,
        row_data: dict[str, DataCell],
        card_templates: dict[str, str],
        inkproc: InkscapeProcess,
        user_script: Callable[["Card"], None],
        selection_type: type["Selection"] = Selection,
        text_bracket_handler: Callable[[re.Match], str] | None = None,
        copies: int = 1,
    ) -> None:
        self.data = row_data
        # Earlier had trouble with deepcopy in another part of the code;
        # for some reason it seemed like the deepcopied DOM had some sort sort
        # of infinite cycle. We'll address this by just getting new copies
        # by reparsing.
        if len(card_templates) == 1:
            for k, v in card_templates.items():
                self.doc = parseString(v)
                break
        else:
            assert "template" in row_data, (
                "Add a `template` column to your data "
                "so that the correct SVG file can be chosen as the card's "
                "template."
            )
            self.doc = parseString(row_data["template"].data)

        self._proc = inkproc
        self.user_script = user_script
        # Pass the Selection class to Card, or if you want to subclass
        # Selection to add more template_funcs or similar, then pass the
        # subclass ("UserSelection" or something like that) instead.
        self.selection_type = type(
            "CardNodeSelection", (selection_type,), {"card": self}
        )
        if text_bracket_handler is not None:
            self.bracket_handler = text_bracket_handler
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
        self._proc.units = self.measurement_units

        # the lock used to break certain Selection methods from running when
        # inside an Inkscape context
        self._lock = False

        # a check to see if any Inkscape context is running:
        self._in_context = False

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
    def root(self) -> Selection:
        root = self.doc.documentElement
        assert root is not None
        return self.selection_type(root)

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

    def parse_inkfile(self) -> None:
        self.inkfile.seek(0)
        self.doc = parse(self.inkfile)
        self.inkfile.seek(0)

    def write_inkfile(self) -> None:
        self.inkfile.seek(0)
        self.inkfile.truncate()
        self.doc.writexml(self.inkfile)
        self.inkfile.flush()

    def inkfile_export(self) -> None:
        # I don't think this truncation before letting Inkscape export is
        # necessary, but I'm adding `seek`, `truncate` and `flush` everywhere
        # I can atm, so here goes.
        self.inkfile.seek(0)
        self.inkfile.truncate()
        self._proc.export_page(self.inkfile.name)
        self.inkfile.seek(0)

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

        if self._in_context:
            raise Exception(
                "Do not create an Inkscape context inside another."
            )

        self._in_context = True

        self.write_inkfile()

        if read_only is not True:
            self._lock = True

        self._proc.load(self.inkfile.name)

        yield self._proc

        # Stuff that should happen when contextmanager releases the yield
        # by `yielding` again... at least I think that's how it works.

        if read_only is not True:
            self._proc.export_page(self.inkfile.name)
            self.parse_inkfile()
            self._lock = False

        self._in_context = False
