from numpy.testing import assert_allclose

from biopharma import ModelComponent, SpecifiedDict
import biopharma.optimisation as opt
from biopharma.specs import Value
from conftest import data_dir


class QuadraticComponent(ModelComponent):
    """A test component that computes a 2nd degree polynomial of its input."""

    INPUTS = {'x': Value(float, 'the input variable')}
    OUTPUTS = {'y': Value(float, 'the function output')}
    PARAMETERS = {
        'a': Value(float, 'the second-degree coefficient'),
        'b': Value(float, 'the first-degree coefficient'),
        'c': Value(float, 'the constant term')
    }

    def __init__(self):
        super().__init__()
        self.data_path = data_dir()
        self.facility = self  # referenced in core component code
        self.load_parameters()

    def run(self):
        x = self.inputs['x']
        self.outputs['y'] = (
            self.parameters['a'] * x * x +
            self.parameters['b'] * x +
            self.parameters['c']
        )

    def true_optimum(self):
        assert self.parameters["a"] != 0
        return -self.parameters["b"] / (2 * self.parameters["a"])


class MultiComponent(ModelComponent):
    """A test component combining multiple independent quadratic components.

    Instead of holding all parameters for the individual components, this
    will have inputs named x1, x2, ...  and ouputs y1, y2, ..., constructed as
    required, and will delegate the computation of each output to each sub-
    component."""

    def __init__(self, *args):
        super().__init__()
        self.data_path = data_dir()
        self.facility = self  # referenced in core component code
        self.input_map = {}
        self.output_map = {}
        self.components = []
        for component in args:
            self.add_component(component)
        # Make the final input and output dicts from the spec
        self.inputs = SpecifiedDict(self.INPUTS, 'input', component=self)
        self.outputs = SpecifiedDict(self.OUTPUTS, 'output', component=self)

    def load_parameters(self):
        pass

    def add_component(self, component):
        self.components.append(component)
        n = len(self.components)
        in_name, out_name = "x{}".format(n), "y{}".format(n)
        # Create new inputs and outputs
        self.INPUTS[in_name] = Value(float, "an input variable")
        self.OUTPUTS[out_name] = Value(float, "an output variable")
        # Link them with the sub-component
        self.input_map[component] = in_name
        self.output_map[component] = out_name

    def run(self):
        """Run all subcomponents by passing their corresponding inputs."""
        for component in self.components:
            component.inputs['x'] = self.inputs[self.input_map[component]]
            component.run()
            self.outputs[self.output_map[component]] = component.outputs['y']

    def true_optimum(self):
        return [comp.true_optimum() for comp in self.components]


class QuadraticGenerator(opt.gen.RangeGenerator):
    """A generator of values constructed so as to include the true solution."""

    def __init__(self, component, width=5):
        assert isinstance(component, QuadraticComponent)
        true_sol = component.true_optimum()
        super().__init__(true_sol - width, true_sol + width)

    # we should set this to draw from real numbers instead of ints (the default)
    # draw_from = random.uniform


def test_optimisation():
    """Test that the optimiser gives expected results for a simple problem."""
    dummy = QuadraticComponent()
    # Pretend that the test component is a facility!
    optimiser = opt.Optimiser(dummy)
    optimiser.add_variable(gen=QuadraticGenerator(dummy),
                           component=opt.sel.facility(), collection='inputs',
                           item='x')
    optimiser.add_objective(component=opt.sel.facility(), item='y',
                            minimise=True)  # assuming a > 0 in params!
    optimiser.run()
    best = optimiser.outputs["bestIndividuals"][0]
    best_sol = best.get_variable('QuadraticComponent', 'x', collection='inputs')
    assert_allclose(best_sol.value, dummy.true_optimum())


def test_multi_optimisation():
    """Test that the optimiser gives expected results for two objectives."""
    dummy_1 = QuadraticComponent()  # Default values for the first component
    # Second component is customised so that its maximum is at x=3
    dummy_2 = QuadraticComponent()
    dummy_2.parameters['a'] = -1.0   # must be floats as they are not coerced
    dummy_2.parameters['b'] = +6.0
    dummy_2.parameters['c'] = -9.0
    # Make optimiser for the combined component
    dummy = MultiComponent(dummy_1, dummy_2)
    optimiser = opt.Optimiser(dummy)
    optimiser.add_variable(gen=QuadraticGenerator(dummy_1),
                           component=opt.sel.facility(), collection='inputs',
                           item='x1')
    optimiser.add_variable(gen=QuadraticGenerator(dummy_2),
                           component=opt.sel.facility(), collection='inputs',
                           item='x2')
    optimiser.add_objective(component=opt.sel.facility(), item='y1',
                            minimise=True)  # assuming a > 0 in params!
    optimiser.add_objective(component=opt.sel.facility(), item='y2',
                            maximise=True)
    # Sometimes the true solution is not reached in 10 generations:
    optimiser.parameters["maxGenerations"] = 20
    optimiser.run()
    best = optimiser.outputs["bestIndividuals"][0]
    best_sol = [best.get_variable('MultiComponent', 'x1', collection='inputs'),
                best.get_variable('MultiComponent', 'x2', collection='inputs')]
    assert_allclose([sol.value for sol in best_sol], dummy.true_optimum())
