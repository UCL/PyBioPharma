"""Specification of Individuals and the genetic makeup (Variables)."""

import copy

import deap.creator


class Variable:
    """Represents a single variable/gene to optimise for a particular Facility."""

    def __init__(self, individual, gen, component, item,
                 collection='parameters', track=None):
        """Create a new variable for the given individual.

        :param individual: the Individual that this is a gene for.
        :param gen: Generator instance that can draw new values for this variable and check
            their validity.
        :param component: a function that takes a Facility instance as argument and returns the
            component in which to set the value of this Variable for that Facility.
        :param item: the name of the item (typically a parameter) within the component to set.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        :param track: how to track statistics for this variable: 'numerical'
            for quantities, 'discrete' for categorical variables, or None for no
            tracking (default).
        """
        self.individual = individual
        self.generator = gen
        self.component_selector = component
        self.item = item
        self.collection = collection
        self.track = track
        self.value = None  # No value drawn yet
        self.name = "{}[{}]".format(self.component.name, self.item)

    @property
    def component(self):
        """Return the component referenced by this variable."""
        return self.component_selector(self.individual.facility)

    def __str__(self):
        """Return a concise representation of this variable for debugging/reporting purposes."""
        return "{}={}".format(self.name, self.generator.describe(self))

    __repr__ = __str__

    def __eq__(self, other):
        """Determine whether two variables represent the same value for the same parameter."""
        return (self.component == other.component and
                self.item == other.item and
                self.collection == other.collection and
                self.value == other.value)

    def __deepcopy__(self, memo):
        """Clone this variable."""
        new = copy.copy(self)
        memo[id(self)] = new
        new.individual = copy.deepcopy(self.individual, memo)
        new.generator = self.generator
        new.component_selector = self.component_selector
        new.item = self.item
        new.collection = self.collection
        new.value = copy.deepcopy(self.value, memo)
        return new

    def update_facility(self):
        """Update our Facility by setting our corresponding field to our value."""
        collection = getattr(self.component, self.collection)
        collection[self.item] = self.value

    def draw(self):
        """Draw a new value for this variable at random."""
        self.value = self.generator.draw(self)
        self.update_facility()

    def repair(self):
        """Alter this variable if it doesn't meet its constraints, so that it does.

        Typically this means re-drawing a valid value at random, but specific generators may
        implement more intelligent routines to choose a similar value.
        """
        if not self.generator.is_valid(self):
            self.generator.repair(self)
            self.update_facility()


class Individual:
    """Encapsulates the genome (variables to optimise) for a single member of the GA population."""

    def __init__(self, optimiser, draw=True):
        """Create a new individual.

        :param optimiser: the Optimiser instance running the GA
        :param draw: whether to generate a random genome on initialisation

        Will create variables for this individual based on the optimiser's spec.
        """
        self.optimiser = optimiser
        self.facility = optimiser.facility
        self.fitness = deap.creator.Fitness()
        self.variables = [klass(self, *args, **kwargs)
                          for (klass, args, kwargs) in optimiser.variable_specs]
        self.error = None
        if draw:
            self.draw()

    def __str__(self):
        """Return a textual representation of this individual for debugging/reporting purposes."""
        return '<Individual 0x{:x}:\n\t{}>\n'.format(
            id(self), '\n\t'.join(map(str, self.variables)))

    __repr__ = __str__

    def __eq__(self, other):
        """Determine whether two individuals have the same genome, i.e. all variables equal."""
        return all(own_var == other_var
                   for (own_var, other_var) in zip(self.variables, other.variables))

    def __deepcopy__(self, memo):
        """Clone this individual.

        We don't clone the facility; it's assumed resetting its parameters is enough to avoid
        conflict between individuals.
        """
        new = copy.copy(self)
        memo[id(self)] = new
        new.optimiser = self.optimiser
        new.facility = self.facility
        new.fitness = copy.deepcopy(self.fitness, memo)
        new.variables = copy.deepcopy(self.variables, memo)
        return new

    def apply_to_facility(self):
        """Update the facility so its parameters match our variables."""
        self.facility.load_parameters()
        for var in self.variables:
            var.update_facility()

    def draw(self):
        """Draw new values for all our variables."""
        self.facility.load_parameters()
        for var in self.variables:
            var.draw()

    def is_valid(self):
        """Determine whether all this individual's variables have valid values."""
        ok = True
        for var in self.variables:
            ok = ok and var.generator.is_valid(var)
        return ok

    def repair(self):
        """Repair any variables that don't meet their constraints, so that they do."""
        self.apply_to_facility()
        for var in self.variables:
            var.repair()

    def has_variable(self, component_name, item, collection='parameters'):
        """Determine whether the requested variable exists.

        :param component_name: the name of the component that the desired Variable modifies.
        :param item: the name of the item (typically a parameter) within the component.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        """
        for var in self.variables:
            if (var.component.name == component_name and var.item == item and
                    var.collection == collection):
                return True
        return False

    def get_variable(self, component_name, item, collection='parameters'):
        """Get one of our variables by name.

        :param component_name: the name of the component that the desired Variable modifies.
        :param item: the name of the item (typically a parameter) within the component.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        """
        for var in self.variables:
            if (var.component.name == component_name and var.item == item and
                    var.collection == collection):
                return var
        raise ValueError('Requested variable not found')


def add_yaml_support():
    """Add support for serialising Individuals to YAML.

    We do not try to serialise all attributes; rather it is assumed that when loading saved
    optimisation results the caller can create a template Individual instance, then just use
    the information saved here to fill in values for the variables, fitness, etc.
    """
    import yaml

    def represent_individual(dumper, ind):
        return dumper.represent_mapping(
            u'!ind',
            {'error': str(ind.error) if ind.error else None,
             'variables': ind.variables,
             'fitness': ind.fitness.values})

    def represent_variable(dumper, var):
        return dumper.represent_mapping(u'!var', {'name': var.name, 'value': var.value})

    for dumper in [yaml.Dumper, yaml.SafeDumper]:
        dumper.add_representer(Individual, represent_individual)
        dumper.add_representer(Variable, represent_variable)

    def construct_individual(loader, node):
        data = loader.construct_mapping(node)
        assert set(data.keys()) == {'error', 'variables', 'fitness'}
        return data

    def construct_variable(loader, node):
        data = loader.construct_mapping(node)
        assert set(data.keys()) == {'name', 'value'}
        return data

    for loader in [yaml.Loader, yaml.SafeLoader]:
        loader.add_constructor(u'!ind', construct_individual)
        loader.add_constructor(u'!var', construct_variable)


add_yaml_support()
