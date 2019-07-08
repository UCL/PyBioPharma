from numpy.random import uniform

from biopharma import ModelComponent, units
import biopharma.optimisation as opt
from biopharma.specs import Q
from conftest import data_dir


class Fussy(ModelComponent):
    """A component that is stable for one parameter value and unstable for others."""
    OUTPUTS = {'y': Q('dimensionless', 'the output (0 or uniformly random)')}
    PARAMETERS = {'p': Q('dimensionless', 'the parameter')}

    def __init__(self, centre, noise):
        """Create a new component.

        :param centre: the stable point of the component. If the parameter p
            matches it, the output will be 0.
        :param noise: the width of a uniform distribution from which the output
            will be drawn if the parameter does not match the stable point.
        """
        super().__init__()
        self.facility = self
        self.data_path = data_dir()
        self.target_centre = centre
        self.noise = noise

    def run(self):
        stable = self.parameters["p"] == self.target_centre
        self.outputs["y"] = 0 if stable else uniform(-self.noise, self.noise)


def test_minimise_variance():
    """Check that minimising the variance of an output works as expected."""
    target = 5 * units("dimensionless")
    # Set up the sensitivity analysis, which will not actually vary anything
    analyser = opt.SensitivityAnalyser(Fussy(target, 100))
    analyser.add_output("y", component=opt.sel.facility(), item="y")
    analyser.parameters["numberOfSamples"] = 10
    # Set up the optimiser to minimise the variance of the output
    optimiser = opt.Optimiser(analyser)
    optimiser.add_variable(gen=opt.gen.RangeGenerator(0 * target, 2 * target),
                           component=opt.sel.facility(),
                           item='p')
    optimiser.add_objective(component=opt.sel.self(),
                            item=("y", "var"),
                            minimise=True)
    optimiser.parameters["maxGenerations"] = 5
    # Run combined optimisation + SA, and check we get the expected result
    optimiser.run()
    best = optimiser.outputs["bestIndividuals"][0]
    assert best.get_variable('Fussy', 'p').value == target
