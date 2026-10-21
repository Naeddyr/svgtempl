import xml.etree.ElementTree as etree
import subprocess

p = subprocess.Popen(
    ["inkscape", "--shell"],
    text=True,
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
)


class InkscapeProcess:
    def __init__(self, process, svgfile...) -> None:
        self.proc = process
        self.file = svgfile
        self.initialize_process

    def initialize_process(...) -> None:
        ...
        # Get rid of the stdout buffer after starting the interactive session,
        # so that we know we're sitting on waiting for input with `> `
        # Maybe check if it's the correct, standard output lines
        
        # Load the file given in self.file
    
    def action(...) -> str:
        ...
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
        return "\n".join(filtered_buffer)
        
    def load(f: file) -> None:
        ...
        # Can you open a file in the interactive thing and it'll replace the old
        # one? Just reuse processes.

card = None

with open("card.svg", "r") as f:
    card = etree.fromstring(f.read())

print(etree.dump(card))
