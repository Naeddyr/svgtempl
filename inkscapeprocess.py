import argparse
import subprocess
import actions as act

from pathlib import Path
from typing import Sequence

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
    def __init__(self, svgfile: Path) -> None:
        self.proc = subprocess.Popen(
            ["inkscape", "--shell"],
            text=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        self.file = svgfile
        self._get_empty_prompt()
        self.load(svgfile)
        print(self.action((("query-all",),)))

    def _get_empty_prompt(self) -> None:
        # Get rid of the stdout buffer after starting the interactive session,
        # so that we know we're sitting on waiting for input with `> `
        # Maybe check if it's the correct, standard output lines

        # Load the file given in self.file

        check_lines: list[str] = []

        self.send()  # make empty prompt line with newline at end

        while True:
            line = self.proc.stdout.readline().strip()
            if line == ">":  # Empty prompt
                break
            check_lines.append(line)

        if check_lines != STARTUP_CHECK:
            for lines in zip(STARTUP_CHECK, check_lines):
                print(lines)
                l, r = lines
                if l != r:
                    print("Above don't match")
            raise Exception(
                f"Inkscape version error? Inkscape shell provided "
                f"unknown lines when starting up: {check_lines=}. "
                f"If things look ok, update STARTUP_CHECK by hand."
            )
        return

    def send(self, action: str = "") -> None:
        print(f"Sending: {action.strip()}")
        self.proc.stdin.write(action.strip() + "\n")
        self.proc.stdin.flush()

    def action(self, actions: Sequence[Sequence[str]]) -> list[str]:
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

        # Actions: maybe handle these as a seq of tuples of strings, instead
        # of as a big string. Join with `";"` here.

        out_lines: list[str] = []

        # action = ";".join((" ".join(s.strip() for s in a),) for a in actions)

        joined = []

        for tup in actions:
            joined.append(tup[0] + ": " + " ".join(s.strip() for s in tup[1:]))

        action = ";".join(joined).strip()

        self.send()  # Just in case
        self.send(action)
        self.send()  # NOT just in case; this is our sentinel

        # Skip first "just in case" empty prompts and other empty prompts
        # until we hit our prompt with our action

        while True:
            line = self.proc.stdout.readline().strip()
            print(f"{line=}")
            print(f"{line in ('>', '')}")
            if not (line in (">", "")):
                print(f"{line=}, '> {action}'")
                if line == f"> {action}":
                    print("MATCH")
                    break  # All's fine
                raise Exception(
                    f"Reading stdout we encountered something that "
                    f"wasn't an empty prompt or our action: '{line}'"
                )

        while True:
            line = self.proc.stdout.readline().strip()
            if line == ">":  # Empty prompt, by just sending a newline
                break
            out_lines.append(line)

        return out_lines

    def load(self, f: Path | str) -> None:
        ret = self.action(
            (
                (
                    act.OPEN,
                    str(f),
                ),
            )
        )
        print(ret)
        return

    def export_page(self, f: Path | str) -> None:
        print(
            self.action(
                (
                    (act.EXPORT_AREA_IS_PAGE,),
                    (act.EXPORT_NAME, str(f)),
                    (act.EXPORT_DO,),
                ),
            )
        )
        return


card = None

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file", type=Path)
    args = argparser.parse_args()
    print(type(args.file), args.file)
    sheet = InkscapeProcess(args.file)

    # with open("card.svg", "r") as f:
    #     card = etree.fromstring(f.read())
    # print(etree.dump(card))
