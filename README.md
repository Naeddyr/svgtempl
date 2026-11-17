# SVGtempl
## Python commandline SVG templater for card games and other SVG graphics

This is a dumb, simple little templating application meant to be used for the creation
of repetitive graphics, like game cards, and outputting them either as images or
printable PDF pages.

This is mainly meant to be an easily-modifiable alternative for Python programmers because
you can't get Nandeck running properly on Linux. It uses pure Python, no external dependencies,
except for Inkscape which is used as a renderer and to do some SVG manipulation.

No GUI, not many presets, and you have to roll a ton of stuff yourself.

### Structure

SVGtempl has two subcommands, `svgtempl init` and `svgtempl run`.

`svgtempl init` is used to initialize basic files in a project folder to get easily started.
It ~~will~~should (WIP) generate:

  * a blank SVG file to be used as a card template
  * a blank ODS spreadsheet file containing rows of templating data
  * a Python user script that is run and which has all the user's instructions
  * a blank SVG page layout template for exporting the cards as printable pages

`svgtempl run` processes the above files and generates images or PDFs.

"Processing" means taking the card template (or WIP: card template variants),
using the user script to program how it is modified based on the data taken
from the spreadsheet.

This is done with simple XML manipulation and Inkscape `actions`.

Inkscape has an 'interactive shell' that you can use for doing batch jobs.
It's exactly the same as running Inkscape `actions` through the command-line with
a flag, except it's a (sub)process with a shell of its own. SVGtempl does some
stupid and probably unwise stuff with this, and it's probably not even that
efficient. Take a look, it's both dumb and neat how dumb it is. I learned a lot.
