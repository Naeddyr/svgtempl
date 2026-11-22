import math
import re

from svgtempl.types import Point, Matrix, Transform
from xml.dom.minidom import Element

TRANSFORM_CALLS_RE = re.compile(r"(\w+)\(([^)]*)\)")


def get_transforms(node: Element) -> Transform:
    #     // calculate delta transform point
    #     var px = deltaTransformPoint(matrix, { x: 0, y: 1 });
    #     var py = deltaTransformPoint(matrix, { x: 1, y: 0 });
    tr_field = node.getAttribute("transform").strip()

    if not tr_field:
        return Transform(0, 0, 0, 0, 0, 0, 0)

    for m in TRANSFORM_CALLS_RE.findall(tr_field):
        call = m.group(1).strip().lowercase()
        params = m.group(2).strip()
        if call == "matrix":
            vals = re.split(r"\s*,\s*|\s*", params)
            matrix_res = Matrix(*(float(s) for s in vals))
        elif call == "":
            ...
        ...

    return Transform(*(map(sum, zip(matrix_res, ...))))


def deltatransform_point(m: Matrix, p: Point) -> Point:
    dx = p.x * m.a + p.y * m.c
    dy = p.x * m.b + p.y * m.d
    return Point(dx, dy)


def decompose_matrix(m: Matrix) -> Transform:
    px = deltatransform_point(..., Point(0, 1))
    py = deltatransform_point(..., Point(1, 0))

    skewx = (180 / math.pi) * math.atan2(px.y, px.x) - 90
    #     // calculate skew
    #     var skewX = ((180 / Math.PI) * Math.atan2(px.y, px.x) - 90);
    #     var skewY = ((180 / Math.PI) * Math.atan2(py.y, py.x));

    #     return {

    #         translateX: matrix.e,
    #         translateY: matrix.f,
    #         scaleX: Math.sqrt(matrix.a * matrix.a + matrix.b * matrix.b),
    #         scaleY: Math.sqrt(matrix.c * matrix.c + matrix.d * matrix.d),
    #         skewX: skewX,
    #         skewY: skewY,
    #         rotation: skewX // rotation is the same as skew x
    #     };
    # }
    return Transform(0, 0, 0, 0, 0, 0, 0)
