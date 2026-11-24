import math
import re

from svgtempl.types import Point, Matrix, Transform
from xml.dom.minidom import Element

# matrix(xyz fsdf sdfsdf)
TRANSFORM_CALLS_RE = re.compile(r"(\w+)\(([^)]*)\)")


# x(asadasd , asdasdas,asdasdas asadasdsad)
# SVG parameters are whitespace and/or comma separate
PARAMS_SPLIT_RE = re.compile(r"\s*[ ,]\s*")


def get_transforms(node: Element) -> tuple[Transform, ...]:
    # Messing with transforms directly in Python seems to be really
    # gd difficult. Rely on Inkscape actions instead. Unfortunately
    # some things need to be done with this, like finding the angle
    # of objects.
    tr_field = node.getAttribute("transform").strip()

    if not tr_field:
        return (Transform(0, 0, 0, 0, 0, 0, 0),)

    transforms = []

    for m in TRANSFORM_CALLS_RE.finditer(tr_field):
        call = m.group(1).strip().lower()
        params = m.group(2).strip()
        vals = list(float(s) for s in PARAMS_SPLIT_RE.split(params))
        if call == "matrix":
            transforms.append(decompose_matrix(Matrix(*vals)))
        elif call == "translate":
            transforms.append(Transform(vals[0], vals[1], 0, 0, 0, 0, 0))
        elif call == "scale":
            if len(vals) == 1:
                transforms.append(Transform(0, 0, vals[0], vals[0], 0, 0, 0))
            else:
                transforms.append(Transform(0, 0, vals[0], vals[1], 0, 0, 0))
        elif call == "skewx":
            transforms.append(Transform(0, 0, 0, 0, vals[0], 0, 0))
        elif call == "skewy":
            transforms.append(Transform(0, 0, 0, 0, 0, vals[0], 0))
        elif call == "rotate":
            if len(vals) == 1:
                transforms.append(Transform(0, 0, 0, 0, 0, 0, vals[0]))
            else:
                rot, x, y = vals[:3]
                transforms.extend(
                    (
                        Transform(x, y, 0, 0, 0, 0, 0),
                        Transform(0, 0, 0, 0, 0, 0, vals[0]),
                        Transform(-x, -y, 0, 0, 0, 0, 0),
                    )
                )

    return tuple(transforms)


def get_rotation(node: Element) -> float:
    sum = 0.0
    for tr in get_transforms(node):
        sum += tr.rot
    return sum


def deltatransform_point(m: Matrix, p: Point) -> Point:
    dx = p.x * m.a + p.y * m.c
    dy = p.x * m.b + p.y * m.d
    return Point(dx, dy)


def decompose_matrix(m: Matrix) -> Transform:
    #     // calculate delta transform point
    #     var px = deltaTransformPoint(matrix, { x: 0, y: 1 });
    #     var py = deltaTransformPoint(matrix, { x: 1, y: 0 });
    px = deltatransform_point(m, Point(0, 1))
    py = deltatransform_point(m, Point(1, 0))

    skewx = (180 / math.pi) * math.atan2(px.y, px.x) - 90
    skewy = (180 / math.pi) * math.atan2(py.y, py.x)
    #     // calculate skew
    #     var skewX = ((180 / Math.PI) * Math.atan2(px.y, px.x) - 90);
    #     var skewY = ((180 / Math.PI) * Math.atan2(py.y, py.x));

    scalex = math.sqrt(m.a * m.a + m.b * m.b)
    scaley = math.sqrt(m.c * m.c + m.d * m.d)

    return Transform(m.e, m.f, scalex, scaley, skewx, skewy, skewx)
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
