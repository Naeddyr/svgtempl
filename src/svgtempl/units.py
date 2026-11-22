from enum import Enum


class Unit(Enum):
    MM = "mm"
    M = "m"
    KM = "km"
    CM = "cm"
    IN = "in"
    PT = "pt"
    PC = "pc"
    PX = "px"
    Q = "Q"
    YD = "yd"
    FT = "ft"


# a dictionary of unit to user unit conversion factors
# from https://inkscapetutorial.org/units-and-coordinate-systems.html
CONVERSIONS = {
    Unit.IN: 96.0,
    Unit.PT: 1.3333333333333333,
    Unit.MM: 3.779527559055118,
    Unit.CM: 37.79527559055118,
    Unit.M: 3779.527559055118,
    Unit.KM: 3779527.559055118,
    Unit.Q: 0.94488188976378,
    Unit.PC: 16.0,
    Unit.YD: 3456.0,
    Unit.FT: 1152.0,
    Unit.PX: 1.0,  # Default px
}
