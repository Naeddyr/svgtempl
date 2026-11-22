from xml.dom.minidom import Element, Text

from svgtempl.text import Style


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
