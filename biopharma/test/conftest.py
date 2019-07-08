
import biopharma as bp
from biopharma import units

import pytest
import py.path
import yaml


def data_dir():
    """Get the path to the data folder for these tests."""
    return py.path.local(__file__).dirpath('data')


def load_data(file_name, folder=None, sections={'inputs', 'outputs'}):
    """Helper function used by the ref_data fixture, that tests can also call directly."""
    if folder is None:
        # Default to the data folder adjacent to this file
        folder = data_dir()
    data_path = folder.join(file_name)
    with data_path.open() as f:
        data = yaml.safe_load(f)
    # Parse all entries as values with units, unless they're booleans!
    for section in sections:
        for key, value in data[section].items():
            if isinstance(value, bool):
                data[section][key] = value
            else:
                data[section][key] = units(str(value))
    return data


@pytest.fixture
def ref_data(request):
    """Fixture for loading reference data from a YAML file."""
    test_name = request.function.__module__
    test_path = request.fspath
    return load_data(test_name[5:] + '_ref.yaml', test_path.dirpath('data'))


def in_units(units):
    """Create a converter function for pandas.read_csv that puts values in the given units."""
    return lambda value: float(value) * units


@pytest.fixture
def product(facility):
    product = bp.Product(facility)
    product.load_parameters()
    return product


@pytest.fixture
def facility():
    """Fixture for creating a basic Facility instance, just enough to test process steps."""
    facility = bp.Facility(str(data_dir()))
    facility.load_parameters()
    return facility


@pytest.fixture
def default_model():
    # Set up the default facility & product to produce
    facility = bp.Facility(str(data_dir()))
    steps = [
    ]
    product = bp.Product(facility, steps)
    facility.load_parameters()
    return facility, product, steps


def show_outputs_for_debugging(outputs, expected, label='Output'):
    """Print out each entry so if a test fails we get more context."""
    for output_name, e_value in sorted(expected.items()):
        actual = outputs[output_name]
        print('{} {}: actual={}, expected={}'.format(label, output_name, actual, e_value))


def check_values(outputs, expected, keys_match=True):
    """Test that dictionary values match those expected."""
    if keys_match:
        assert set(outputs.keys()) == set(expected.keys())
    for output_name, e_value in expected.items():
        actual = outputs[output_name]
        if type(actual) is bool:
            assert actual == e_value
        else:
            assert actual.units == e_value.units
            assert actual.magnitude == pytest.approx(e_value.magnitude)  # rel tol = 1e-6 = 1e-4 %
