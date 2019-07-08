
from biopharma import units, util


def test_round_integers():
    assert util.round(3 * units.m, units.m) == 3 * units.m
    assert util.round(-5 * units.s, units.s) == -5 * units.s


def test_round_easy_non_integers():
    assert util.round(1.2 * units.s, units.s) == 1 * units.s
    assert util.round(-11.2 * units.s, units.s) == -11 * units.s
    assert util.round(3.7 * units.s, units.s) == 4 * units.s
    assert util.round(-99.9 * units.s, units.s) == -100 * units.s


def test_round_unit_converts():
    assert util.round(4 * units.cm, units.m) == 0 * units.m
    assert util.round(66 * units.cm, units.m) == 1 * units.m


def test_round_midpoints_away_from_zero():
    assert util.round(3.5 * units.m, units.m) == 4 * units.m
    assert util.round(-2.5 * units.m, units.m) == -3 * units.m


def test_ceil_easy_cases():
    assert util.ceil(4 * units.h, units.h) == 4 * units.h
    assert util.ceil(-4 * units.h, units.h) == -4 * units.h
    assert util.ceil(4.4 * units.h, units.h) == 5 * units.h
    assert util.ceil(-4.4 * units.h, units.h) == -4 * units.h
    assert util.ceil(6.6 * units.h, units.h) == 7 * units.h
    assert util.ceil(-6.6 * units.h, units.h) == -6 * units.h


def test_ceil_unit_converts():
    assert util.ceil(3 * units.g, units.kg) == 1 * units.kg
    assert util.ceil(-123 * units.cm, units.m) == -1 * units.m


def test_floor_easy_cases():
    assert util.floor(4 * units.h, units.h) == 4 * units.h
    assert util.floor(-4 * units.h, units.h) == -4 * units.h
    assert util.floor(4.4 * units.h, units.h) == 4 * units.h
    assert util.floor(-4.4 * units.h, units.h) == -5 * units.h
    assert util.floor(6.6 * units.h, units.h) == 6 * units.h
    assert util.floor(-6.6 * units.h, units.h) == -7 * units.h


def test_floor_unit_converts():
    assert util.floor(3 * units.g, units.kg) == 0 * units.kg
    assert util.floor(-123 * units.cm, units.m) == -2 * units.m


def test_trunc_easy_cases():
    assert util.trunc(4 * units.h, units.h) == 4 * units.h
    assert util.trunc(-4 * units.h, units.h) == -4 * units.h
    assert util.trunc(4.4 * units.h, units.h) == 4 * units.h
    assert util.trunc(-4.4 * units.h, units.h) == -4 * units.h
    assert util.trunc(6.6 * units.h, units.h) == 6 * units.h
    assert util.trunc(-6.6 * units.h, units.h) == -6 * units.h


def test_trunc_unit_converts():
    assert util.trunc(3 * units.g, units.kg) == 0 * units.kg
    assert util.trunc(-123 * units.cm, units.m) == -1 * units.m
