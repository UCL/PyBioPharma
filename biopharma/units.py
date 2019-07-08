"""This module defines a common units registry for the project."""

from contextlib import closing
from io import StringIO
import pkg_resources

import pint


__all__ = ['units']


units = pint.UnitRegistry()

# Load our units definitions from file, even if we're an installed package
with closing(pkg_resources.resource_stream(__name__, 'units.txt')) as fp:
    rbytes = fp.read()
units.load_definitions(StringIO(rbytes.decode('utf-8')))
units.enable_contexts('currency')
