"""Optimisation functionality for the PyBioPharma framework.

This package contains code for running Genetic Algorithm optimisation of models
implemented using PyBioPharma.
"""

# Import key sub-modules so users can just do 'from biopharma import optimiser'
from . import gen                 # noqa
from . import sel                 # noqa
from . import dist                # noqa
from .optimiser import Optimiser, Tracking  # noqa
from .sensitivity import SensitivityAnalyser  # noqa
