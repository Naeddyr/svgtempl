import subprocess

from svgtempl.actions import Act
from svgtempl.units import CONVERSIONS, Unit
from pathlib import Path
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from svgtempl.card import Card

STARTUP_CHECK = [
    (
        "Inkscape interactive shell mode. Type 'action-list' "
        "to list all actions. Type 'quit' to quit."
    ),
    "Input of the form:",
    "action1:arg1; action2:arg2; ...",
    "Only actions that don't require a desktop may be used.",
]


class InkscapeProcess:
    def __init__(self, svgfile: Path, card: "Card" | None = None) -> None:
        self.proc = subprocess.Popen(
            ["inkscape", "--shell"],
            text=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.file = svgfile
        self.card = card
        self.stdout: IO[str] = self.proc.stdout  # type: ignore[assignment]
        assert self.stdout is not None
        self.stdin: IO[str] = self.proc.stdin  # type: ignore[assignment]
        assert self.stdin is not None
        # Convert data from query- actions (default: px) into SVG document
        # measurement unit (`mm` usually)
        self.units = Unit.PX
        self._get_empty_prompt()
        self.load(svgfile)

    def __del__(self) -> None:
        # self.action() will BLOCK on return if it tries to wait for messages,
        # so it will always return an empty list when quitting
        self.action(Act.QUIT)

    def _get_empty_prompt(self) -> None:
        # Get rid of the stdout buffer after starting the interactive session,
        # so that we know we're sitting on waiting for input with `> `
        # Maybe check if it's the correct, standard output lines

        # Load the file given in self.file

        check_lines: list[str] = []

        self.send()  # make empty prompt line with newline at end

        while True:
            line = self.stdout.readline().strip()
            if line == ">":  # Empty prompt
                break
            check_lines.append(line)

        if check_lines != STARTUP_CHECK:
            for lines in zip(STARTUP_CHECK, check_lines):
                l, r = lines
                if l != r:
                    print(f"Lines do not match: {l=}, {r=}")
            raise Exception(
                f"Inkscape version error? Inkscape shell provided "
                f"unknown lines when starting up: {check_lines=}. "
                f"If things look ok, update STARTUP_CHECK by hand."
            )
        return

    def send(self, action: str = "") -> None:
        self.stdin.write(action.strip() + "\n")
        self.stdin.flush()

    def action(
        self,
        *actions: Act | str,
        no_lock_check=False,
    ) -> list[str]:
        # 1. Send action to stdout, flush.
        # 2. Immediately send newline + flush to force a blank prompt that we
        # can use to determine that the stuff we did finished and that we're
        # waiting on waiting for input. Why send the newline? Because that way
        # we can be sure that a line with only `> ` is a legit prompt, and not
        # get blocked. It's easier this way, and we can use readline() for it.
        # 3. Readline() into a line buffer until we hit the empty prompt.
        # 4. Return the line buffer as output, skipping prompts

        # When looping over stdout, stop at empty prompts. If there are extra
        # empty prompts for some reason, loop over them only when you are 100%
        # sure there's going to be some kind of content in the future (from
        # writing input into stdin as a an action)

        if (
            self.card is not None
            and self.card._lock is False
            and no_lock_check is False
        ):
            raise Exception(
                "Did you mean to run this action outside of an "
                "Inkscape context? "
                "Use Inkscape.action(..., unlock=True) if so."
            )

        out_lines: list[str] = []

        assert len(actions) > 0
        assert isinstance(actions[0], Act)

        joined = []
        cur_actions = []
        cur_action: list[Act | str] = []

        for x in actions:
            if isinstance(x, Act):
                if len(cur_action) > 0:
                    cur_actions.append(cur_action)
                    cur_action = []
            cur_action.append(x)
        cur_actions.append(cur_action)

        for cur_action in cur_actions:
            if len(cur_action) == 1:
                # This is needed for certain issues: for example, typing
                # `quit:`  into the interactive shell will stall until you
                # ^C.
                joined.append(str(cur_action[0]))
            elif len(cur_action) > 0:
                joined.append(
                    f"{cur_action[0]}: "
                    + " ".join(str(s).strip() for s in cur_action[1:])
                )

        action = ";".join(joined).strip()

        self.send()  # Just in case
        self.send(action)
        self.send()  # NOT just in case; this is our sentinel

        if "quit" in action:
            return []

        # Skip first "just in case" empty prompts and other empty prompts
        # until we hit our prompt with our action
        # THIS WILL BLOCK ON QUIT
        while True:
            line = self.stdout.readline().strip()
            if not (line in (">", "")):
                if line == f"> {action}":
                    break  # All's fine
                raise Exception(
                    f"Reading stdout we encountered something that "
                    f"wasn't an empty prompt or our action: '{line}'"
                )

        while True:
            line = self.stdout.readline().strip()
            if line == ">":  # Empty prompt, by just sending a newline
                break
            out_lines.append(line)

        return out_lines

    def query(self) -> dict[str, dict[str, float]]:
        queries = self.action(Act.QUERY_ALL)

        # unit conversion code WIP
        conv = CONVERSIONS[self.units]

        ret = {}
        for line in queries:
            if not line:
                continue
            id, x, y, width, height = line.split(",")
            ret[id] = {
                "x": float(x) / conv,
                "y": float(y) / conv,
                "width": float(width) / conv,
                "height": float(height) / conv,
            }

        return ret

    def current_selection(self) -> list[str]:
        ret = []
        text = self.action(Act.PRINT_SELECT)

        # Lines look like
        # rect1 cloned: false ref: 1 href: 0 total href: 0
        # path1 cloned: false ref: 1 href: 0 total href: 0
        for line in text:
            if words := line.split():
                ret.append(words[0])

        return ret

    def clear(self) -> None:
        self.action(Act.SELECT_CLEAR)

    def load(self, f: Path | str) -> None:
        # Can't annotate the output of NamedTemporaryFile, so just remember
        # to pass the `.name` property when using them.
        assert isinstance(f, (Path, str)), (
            f"Argument {f=} is not a Path or "
            f"string, did you pass a file "
            f"by mistake?"
        )

        res = self.action(
            Act.OPEN,
            str(f),
        )

        if len(res) > 0:
            print("\n".join(res))
            raise Exception("File failed to parse.")

        return

    def export_page(self, f: Path | str) -> None:
        self.action(
            Act.EXPORT_AREA_IS_PAGE,
            Act.EXPORT_NAME,
            str(f),
            Act.EXPORT_DO,
        )
        return
