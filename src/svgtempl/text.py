import re
from enum import Flag, auto

FORMATTING_CHARS_RE = re.compile(r"(\\.|\\$|\*|_)")


class Style(Flag):
    NONE = 0
    BOLD = auto()
    ITALIC = auto()


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
