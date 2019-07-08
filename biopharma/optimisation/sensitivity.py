
import biopharma as bp
from biopharma.server.tasks import SoftTimeLimitExceeded
from biopharma.specs import Value, Nested, Q
from .individual import Variable
from .dist import DistributionGenerator
from .util import get_item


class SensitivityVariable(Variable):
    """Represents a variable or uncertain aspect of a particular Facility."""

    def __init__(self, facility, component, item, collection, gen, **kwargs):
        assert isinstance(gen, DistributionGenerator)
        self.gen = gen
        self._setup(facility, component, item, collection)

    def _setup(self, facility, component, item, collection):
        self.facility = facility
        self.component_selector = component
        self.item = item
        self.collection = collection
        self.value = None  # No value drawn yet
        self.name = "{}[{}]".format(self.component.name, self.item)

    @property
    def component(self):
        """Return the component referenced by this variable."""
        return self.component_selector(self.facility)

    def __str__(self):
        """Return a concise representation of this variable for debugging/reporting purposes."""
        return self.name

    __repr__ = __str__

    def draw(self):
        """Draw a new value for this variable at random."""
        self.value = self.gen.draw()

    def repair(self):
        """Alter this variable if it doesn't meet its constraints, so that it does."""
        # TODO Think about whether this is needed.
        pass

    def __deepcopy__(self, memo):
        """Clone this variable."""
        # TODO Think about whether this is needed (copied from optimisation,
        # where it was used to generate new populations).
        import copy
        new = copy.copy(self)
        memo[id(self)] = new
        new.gen = self.gen
        new.facility = copy.deepcopy(self.facility, memo)
        new.item = self.item
        new.collection = self.collection
        new.value = copy.deepcopy(self.value, memo)
        return new


class SensitivityAnalyser(bp.AnalysisComponent):
    """Monte Carlo sensitivity analysis for PyBioPharma models."""

    PARAMETERS = {
        'numberOfSamples': Value(int, 'How many Monte Carlo samples to take')
    }

    def __init__(self, facility, **kwargs):
        super(SensitivityAnalyser, self).__init__(**kwargs)
        self.facility = facility
        self.variables = []
        self.output_desc = {}
        self.load_parameters()
        self.OUTPUTS['seed'] = Value(tuple, 'The initial state of the random number generator')
        self.OUTPUTS['failed_runs'] = Value(int, 'How many Monte Carlo runs failed to complete')

    def add_variable(self, component, item, collection='parameters', gen=None):
        """Add an aspect to be varied in the sensitivity analysis.

        :param facility: the Facility that this describes.
        :param component: a function that takes a Facility instance as argument and returns the
            component in which to set the value of this Variable for that Facility.
        :param item: the name of the item (typically a parameter) within the component to set.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        :param gen: a generator for the distribution of the variable's values.
        """
        try:  # TODO better error reporting and specific exception type
            var = SensitivityVariable(self.facility, component, item, collection,
                                      gen)
        except Exception as e:
            print("Could not add variable. Error:")
            print(e)
        else:
            self.variables.append(var)

    def add_output(self, name, component, item, collection='outputs'):
        """Add a new output of which to analyse the sensitivity.

        :param name: the name by which to refer to this output.
        :param component: a function that takes a Facility instance as argument and returns the
            component in which to look for the value of this output for that Facility.
        :param item: the name of the item (typically an output) within the component to use as
            the output.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        """
        # Get the units of the output
        comp = component(self.facility)
        spec = get_item(getattr(comp, collection).spec, item)
        # Update the output specification
        self.OUTPUTS[name] = self._make_spec(name, spec)
        # Record how to compute the output
        self.output_desc[name] = {'component': component, 'item': item,
                                  'collection': collection}

    def run(self):
        # Initialise outputs (we must do this because the OUTPUTS specification
        # was not known when the analyser was constructed, hence the outputs
        # dictionary will not have the correct spec). This seems better than
        # doing this as part of add_output, as it will call the right methods
        # (including _setup) on the SpecifiedDict only once.
        self.outputs = bp.SpecifiedDict(self.OUTPUTS, 'output', component=self)
        for name in self.outputs:
            self.outputs[name]['min'] = self.OUTPUTS[name].nested['min'].inf
            self.outputs[name]['max'] = -self.OUTPUTS[name].nested['max'].inf
            self.outputs[name]['avg'] = self.OUTPUTS[name].nested['avg'].zero
            self.outputs[name]['var'] = self.OUTPUTS[name].nested['var'].zero
            self.outputs[name]['all'] = []
        # Record the seed:
        initial_seed = self.get_seed()
        self.outputs['seed'] = initial_seed
        # Run the sensitivity analysis:
        n_runs = self.parameters['numberOfSamples']
        print("Starting {} Monte Carlo runs.".format(n_runs), end='')
        self.outputs['failed_runs'] = 0
        i = 1
        while i <= n_runs:
            for var in self.variables:
                # Choose a value for each variable and apply it to the facility
                var.draw()
                var.update_facility()
            # Evaluate the facility, updating the statistics for each output
            try:
                self.facility.run()
            except SoftTimeLimitExceeded:
                raise
            except Exception:
                self.outputs['failed_runs'] += 1
            else:
                # Get output and update stats
                for name, desc in self.output_desc.items():
                    component = desc['component'](self.facility)
                    collection = getattr(component, desc['collection'])
                    value = get_item(collection, desc['item'])
                    out = self.outputs[name]
                    out['min'] = min(out['min'], value)
                    out['max'] = max(out['max'], value)
                    # New mean and variance can be calculated online
                    old_avg = out['avg']
                    out['avg'] = old_avg + (value - old_avg) / i
                    out['var'] = ((i - 1) * out['var'] +
                                  (value - old_avg) * (value - out['avg'])) / i
                    out['all'].append(value)
            print('.', end='')
            i += 1
        print("Done!")
        if self.outputs["failed_runs"] == n_runs:
            raise bp.BiopharmaError("All Monte Carlo runs failed.")

    def _make_spec(self, var_name, spec):
        """Create the specification for an output variable of the analysis."""
        assert isinstance(spec, Q)
        base_dict = {
            'min': spec.with_same_units('The minimum value for ' + var_name),
            'max': spec.with_same_units('The maximum value for ' + var_name),
            'avg': spec.with_same_units('The average value for ' + var_name),
            'var': spec.with_squared_units('The variance for ' + var_name),
            'all': Value(list, 'All the samples taken for ' + var_name)
        }
        return Nested(base_dict, 'Sensitivity statistics for ' + var_name)
