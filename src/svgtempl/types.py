from typing import NamedTuple


class Transform(NamedTuple):
    transx: float
    transy: float
    scalex: float
    scaley: float
    skewx: float
    skewy: float
    rot: float


class Matrix(NamedTuple):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


class Point(NamedTuple):
    x: float
    y: float
