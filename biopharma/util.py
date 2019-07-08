
import math

__all__ = ['round', 'ceil', 'floor', 'trunc']


def round(quantity, units):
    """The legacy code rounds midpoints away from zero, while Python 3 uses IEEE default mode.

    :param quantity: the quantity to round
    :param units: the units to convert to before rounding, and of the result
    """
    number = quantity.to(units).magnitude
    if number < 0:
        return math.ceil(number - 0.5) * units
    else:
        return math.floor(number + 0.5) * units


def ceil(quantity, units):
    """Compute the ceiling of a quantity with units.

    :param quantity: the quantity to take the ceiling of
    :param units: the units to convert to before taking the ceiling, and of the result
    :returns: the ceiling of quantity, measured in units
    """
    number = quantity.to(units).magnitude
    return math.ceil(number) * units


def floor(quantity, units):
    """Compute the floor of a quantity with units.

    :param quantity: the quantity to take the ceiling of
    :param units: the units to convert to before taking the ceiling, and of the result
    :returns: the ceiling of quantity, measured in units
    """
    number = quantity.to(units).magnitude
    return math.floor(number) * units


def trunc(quantity, units):
    """Truncate a floating point value by discarding all decimal digits.

    :param quantity: the quantity to truncate
    :param units: the units to convert to before truncating, and of the result
    :returns: the truncated quantity, measured in units
    """
    number = quantity.to(units).magnitude
    return math.trunc(number) * units
