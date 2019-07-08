
"""Wrappers around the BioPharma modelling components for use by the server."""

import biopharma as bp


def create_default():
    """Create a default model configuration.

    :returns: a tuple (optimiser, steps)
    """
    facility = create_facility()
    optimisation_base = create_analyser(facility)
    optimiser = create_optimiser(optimisation_base)
    product = facility.products[0]
    return optimiser, product.sequence.steps


def create_facility():
    """Create a template facility instance.

    This defines a facility with the canonical process sequence for a single product.
    """
    facility = bp.Facility(data_path=get_data_dir())
    steps = []
    bp.Product(facility, steps)
    facility.load_parameters()
    return facility


def create_optimiser(component):
    """Create an optimiser instance for the given component (facility or
    sensitivity analyser).

    No setup will be performed, i.e. no variables to optimise or objectives set.
    """
    from biopharma import optimisation as opt

    optimiser = opt.Optimiser(component)
    return optimiser


def create_analyser(facility):
    """Create a sensitivity analyser instance for the given facility.

    No setup will be performed, i.e. no variables to optimise or objectives set.
    """
    from biopharma import optimisation as opt

    analyser = opt.SensitivityAnalyser(facility)
    return analyser


def get_data_dir():
    """Get a filesystem path to a suitable data folder for the facility.

    This uses pkg_resources to extract the data folder installed with the
    biopharma package, working even if it's installed as an egg.

    TODO: Check whether we need to arrange cleanup of the extracted folder.
    """
    import pkg_resources
    path = pkg_resources.resource_filename('biopharma', '../data')
    print(path)
    return path
