# PyBioPharma

*Modelling and optimisation of biopharma processes, in Python.*

This is a work-in-progress generalisation of a process economics modelling
framework. It includes support for genetic algorithm optimisers, sensitivity
analysis, and semi-automatically generated web interfaces. The framework is
designed to be flexible, so that researchers can represent their own models
of similar processes, and use this software for model analysis.

**Note**: this version has been 'generalised' just by cutting out all
model-specific details. It is thus in a semi-broken state. None of the
notebooks will run as written, and most of the tests will fail. Time
and interest permitting all this could, of course, be fixed.

## Installation

This modelling framework requires Python to run. We also recommend using
Git for obtaining this software and tracking changes you make when working
with your models. Detailed instructions can be found in the file
[docs/install.md](docs/install.md).

## Usage

Usage instructions for modellers are given in the file
[docs/usage.md](docs/usage.md). This includes information on how to run
simulations of the existing models, optimise parameter values, and change
the model equations.
