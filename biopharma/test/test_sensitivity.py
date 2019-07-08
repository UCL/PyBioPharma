import numpy as np
from numpy.testing import assert_allclose
import pytest

from biopharma import BiopharmaError, ModelComponent, units
import biopharma.optimisation as opt
from biopharma.specs import Q
from conftest import data_dir


class Doubler(ModelComponent):
    """A toy component that computes double its input."""
    INPUTS = {'x': Q('dimensionless', 'the input variable')}
    OUTPUTS = {'y': Q('dimensionless', 'twice the input')}

    def __init__(self):
        super().__init__()
        self.data_path = data_dir()
        self.facility = self  # referenced in core component code

    def run(self):
        self.outputs["y"] = 2 * self.inputs["x"]


def test_sensitivity_running():
    """Check that the results are as expected for a simple model."""
    doubler = Doubler()
    limit = 5 * units("dimensionless")
    sa = opt.SensitivityAnalyser(doubler)
    sa.add_variable(gen=opt.dist.Uniform(-limit, limit),
                    component=opt.sel.facility(),
                    collection="inputs",
                    item="x")
    sa.add_output("y", component=opt.sel.facility(), item="y")
    sa.parameters["numberOfSamples"] = 1000
    sa.run()
    output = sa.outputs["y"]
    # From properties of uniform distribution: Min and max should be twice that
    # of the input; mean should be the same (0), variance 4 times as much.
    # Note that checks are quite tolerant, as we are unlikely to get exact
    # matches without more samples.
    # Also note that assert_allclose does not do any unit conversion, but seems
    # to just consider the magnitude. This is not a problem here as the spec is
    # dimensioness, but it's worth keeping in mind if the tests change!
    assert_allclose(output["min"], -2 * limit, rtol=0.1)
    assert_allclose(output["max"], 2 * limit, rtol=0.1)
    # This test uses absolute tolerance because the target value is 0,
    # and relative tolerance is therefore meaningless
    # TODO better to switch target and actual values around?
    assert_allclose(output["avg"], 0, atol=0.5)
    input_var = limit * limit / 3  # var = (max-min)^2 / 12 = 4 * limit^2 / 12
    assert_allclose(output["var"], 4 * input_var, rtol=0.1)


def test_sensitivity_analyser_statistics(default_model):
    """Check that the computed statistics are consistent with the samples."""
    facility, product, steps = default_model
    sa = opt.SensitivityAnalyser(facility)
    param_mean = facility.products[0].parameters["param"]
    param_width = 2 * param_mean.units
    sa.add_variable(
        gen=opt.dist.Uniform(param_mean - param_width,
                             param_mean + param_width),
        component=opt.sel.product(),
        item="param")
    sa.add_output("CoG", component=opt.sel.product(0), item="cogs")
    n_samples = 10  # to speed up test
    sa.parameters["numberOfSamples"] = n_samples
    sa.run()
    output = sa.outputs["outputs"]
    # Lists of quantities don't work well with NumPy, unless changed like this:
    samples = ([sample.magnitude for sample in output["all"]] *
               output["all"][0].units)  # samples have same units, as per spec
    # Check that the correct number of samples is produced
    assert len(samples) == n_samples
    # Check that statistics are correctly computed
    assert output["min"] == np.min(samples)
    assert output["max"] == np.max(samples)
    assert_allclose(output["avg"], np.mean(samples))
    assert_allclose(output["var"], np.var(samples))


def test_sensitivity_error_if_all_failed():
    """Check that an error is thrown if no runs are successful."""
    doubler = Doubler()
    sa = opt.SensitivityAnalyser(doubler)
    sa.parameters["numberOfSamples"] = 0
    with pytest.raises(BiopharmaError):
        sa.run()
