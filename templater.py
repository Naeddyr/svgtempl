import argparse
import xml.etree.ElementTree as etree
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
    "action1:arg1; action2:arg2; verb1; verb2; ...",
    "Only verbs that don't require a desktop may be used.",
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
        self._initialize_process()

    def _initialize_process(self) -> None:
        ...
        # Get rid of the stdout buffer after starting the interactive session,
        # so that we know we're sitting on waiting for input with `> `
        # Maybe check if it's the correct, standard output lines

        # Load the file given in self.file

    def send(self, action: str = "") -> None:
        self.proc.write(action.strip() + "\n")

    def action(self, action: str, rest: list[str]) -> list[str]:
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

        filtered_out_lines: list[str] = []

        action = action.strip()

        self.send()  # Just in case
        self.send(action)
        self.send()  # NOT just in case; this is our sentinel

        # Skip first "just in case" empty prompts and other empty prompts
        # until we hit our prompt with our action

        for line in self.proc.stdout.readlines():
            line = line.strip()
            if not (line in (">", "")):
                if line == f"> {action}":
                    break  # All's fine
            raise Exception(f"Reading stdout we encountered something that "
                            f"wasn't an empty prompt or our action: '{line}'")

        for line in self.proc.stdout.readlines():
            line = line.strip()
            if line == ">":
                break
            filtered_out_lines.append(line)

        return filtered_out_lines

    def load(f: Path) -> None:
        ...
        # Can you open a file in the interactive thing and it'll replace the old
        # one? Just reuse processes.


card = None

with open("card.svg", "r") as f:
    card = etree.fromstring(f.read())

print(etree.dump(card))
