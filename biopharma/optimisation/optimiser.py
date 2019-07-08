"""The main Optimiser class."""

import biopharma as bp
from biopharma.server.tasks import SoftTimeLimitExceeded
from biopharma.specs import Value, Table, in_units
from .individual import Individual, Variable
from .util import get_item, with_units

import numbers
import random
from enum import Enum

import deap.base
import deap.creator
import deap.tools
import numpy as np

__all__ = ['Optimiser', 'Tracking']


class Optimiser(bp.AnalysisComponent):
    """Genetic algorithm-based optimisation for PyBioPharma models.

    TODO: Some documentation on how to do optimisation.
    """

    PARAMETERS = {
        'populationSize': Value(
            int, 'How many individual facilities to evaluate in each population'),
        'maxGenerations': Value(
            int, 'How many generations of the genetic algorithm to run'),
        'crossoverProbability': Value(
            float, 'Probability that genetic crossover occurs between 2 individuals'),
        'geneCrossoverProbability': Value(
            float, 'If crossover occurs, probability that any single gene will be swapped'),
        'mutationRate': Value(
            float, 'Average number of genes in an individual that will mutate each generation'),
    }

    OUTPUTS = {
        'finalPopulation': Value(list, 'The final population from the genetic algorithm'),
        'bestIndividuals': Value(list, 'All non-dominated individuals'),
        'bestObjectiveValues': Value(list, 'The fitness(es) recorded for the best individual(s)'),
        'seed': Value(tuple, 'The initial state of the random number generator for this run')
    }

    def __init__(self, base_component, **kwargs):
        """Create a new optimiser.

        :param base_component: the base component on which to run the optimiser
            (typically, the Facility to optimise).
        :param kwargs: further keyword arguments are passed to ModelComponent.__init__, notably
            name and param_filename.
        """
        super(Optimiser, self).__init__(**kwargs)
        self.base = base_component
        self.facility = self.base.facility
        self.variable_specs = []
        self.all_stats = {}
        self.objectives = []
        self.debug = False
        self.load_parameters()

    def add_variable(self, klass=Variable, *args, **kwargs):
        """Add a 'gene' specification that can vary across individuals.

        :param klass: the class of Variable to use, in case a subclass is desired.
        :param args: positional arguments to use when constructing instances of the class.
        :param kwargs: keyword arguments to use when constructing instances of the class.
        """
        assert issubclass(klass, Variable)
        self.variable_specs.append((klass, args, kwargs))

    def add_objective(self, component, item, collection='outputs',
                      minimise=False, maximise=False, weight=1.0):
        """Add a new objective to optimise for.

        :param component: a function that takes a Facility instance as argument and returns the
            component in which to look for the value of this objective for that Facility.
        :param item: the name of the item (typically an output) within the component to use as
            the objective value.
        :param collection: which collection (i.e. inputs, parameters, or outputs) to look for
            item in.
        :param minimise: set to True if this objective should be minimised.
        :param maximise: set to True if this objective should be maximised.
        :param weight: can be used in multi-objective optimisation to make some objectives more
            important than others. Should be a positive real number.

        Exactly one of minimise or maximise must be set to True.
        """
        assert minimise or maximise
        assert not (minimise and maximise)
        if minimise:
            weight = -weight
        self.objectives.append({
            'component': component, 'item': item, 'collection': collection, 'weight': weight})

    def run(self):
        """Run an optimisation.

        Uses elitist single-objective or multi-objective GA at present.
        """
        print('Running optimiser for {} generations with {} individuals'.format(
            self.parameters['maxGenerations'], self.parameters['populationSize']))
        # Reset the facility
        self.facility.load_parameters()
        # Record the current state of the random number generator
        initial_seed = self.get_seed()
        self.outputs['seed'] = initial_seed
        if self.debug:
            print("RNG state:", initial_seed)

        # Initialise the GA tools
        self._initialise()
        toolbox = self.toolbox
        params = self.parameters
        stats = self.stats
        logbook = self.logbook

        # Create and evaluate initial population
        pop = toolbox.population(n=params['populationSize'])
        fitnesses = toolbox.map(toolbox.evaluate, pop)
        for ind, fitness in zip(pop, fitnesses):
            ind.fitness.values = fitness
        print()

        # Run generations
        for gen in range(params['maxGenerations']):
            # Record statistics for this generation
            logbook.record(gen=gen, **stats.compile(pop))
            print('Evolving generation', gen)
            if self.debug:
                print(pop)

            # Select offspring for the next generation, and clone them
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < params['crossoverProbability']:
                    toolbox.mate(child1, child2)
                    # Invalidate the old fitness values
                    del child1.fitness.values
                    del child2.fitness.values
            for mutant in offspring:
                toolbox.mutate(mutant)
                del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            print()

            # The new population takes the best half of pop + offspring
            pop = toolbox.selectNewPop(pop + offspring, len(pop))

        # Record statistics for the final generation
        logbook.record(gen=gen + 1, **stats.compile(pop))

        # Save outputs
        outputs = self.outputs
        outputs['finalPopulation'] = pop
        outputs['bestIndividuals'] = self.best_individuals(pop)
        outputs['bestObjectiveValues'] = [ind.fitness.values for ind in outputs['bestIndividuals']]
        print('Optimisation done!')

    def best_individuals(self, pop):
        """Return the best individuals in the given population.

        Finds those that have the best score in at least one objective. There
        will thus be at most k individuals returned, where k is the number of
        objectives.

        :param pop: a list of individuals, assumed to be sorted by fitness
        :returns: a list of the 'best' individuals within pop
        """
        best = []
        for i, obj in enumerate(self.objectives):
            best_i = None
            for ind in pop:
                if best_i is None or (ind.fitness.values[i] * obj['weight'] >
                                      best_i.fitness.values[i] * obj['weight']):
                    best_i = ind
            best.append(best_i)
        # We now need to remove duplicates and maintain the same ordering as in pop.
        # It's non-trivial to hash individuals (and they're mutable), so we can't use a set.
        # Even using the 'in' operator doesn't help as different objects with the same genome
        # are treated as distinct!
        # Instead we need to compare explicitly with ==
        deduped = []
        for ind in pop:
            if ind in best:
                for existing in deduped:
                    if ind == existing:
                        break
                else:
                    deduped.append(ind)
        assert len(deduped) <= len(self.objectives)  # Paranoia
        return deduped

    def save_results(self):
        """Return key result information as a YAML text string.

        This is suitable for being reloaded by load_results().
        """
        import yaml
        return yaml.dump(self.extract_outputs())

    def load_results(self, stream):
        """Load details of the final population saved by save_results.

        The save_results method will serialise key information about individuals
        to a YAML document (text string). This method, if passed this data and
        called on an Optimiser with the same objectives and variable definitions,
        will reconstruct an equivalent outputs dictionary to the original optimiser.

        This is primarily for use by the web interface, which needs to analyse the
        results of saved experiments, but could be of utility to researchers using
        the code directly as well.

        :param stream: string or open file with YAML data
        """
        self._initialise()

        import yaml
        loaded = yaml.safe_load(stream)

        # Simple outputs copy directly
        outputs = self.outputs
        for name in ['bestObjectiveValues', 'seed']:
            outputs[name] = loaded[name]

        # For individuals we need to reconstruct proper objects
        individuals = {}
        for ind_data in loaded['finalPopulation']:
            ind = individuals[id(ind_data)] = Individual(self, draw=False)
            ind.error = ind_data['error']
            ind.fitness.values = ind_data['fitness']
            for var, var_data in zip(ind.variables, ind_data['variables']):
                assert var_data['name'] == var.name
                collection = getattr(var.component, var.collection)
                spec = collection.spec[var.item]
                var.value = spec.parse(var_data['value'])
        outputs['finalPopulation'] = [individuals[id(ind_data)]
                                      for ind_data in loaded['finalPopulation']]
        outputs['bestIndividuals'] = [individuals[id(ind_data)]
                                      for ind_data in loaded['bestIndividuals']]

    # Below here are methods not intended for direct use by users.

    def _initialise(self):
        """Prepare to run an optimisation."""
        self._setup_toolbox()
        # Set up the Fitness class for individuals to use
        if hasattr(deap.creator, 'Fitness'):
            del deap.creator.Fitness
        weights = [obj['weight'] for obj in self.objectives]
        deap.creator.create('Fitness', deap.base.Fitness, weights=weights)
        # Determine a 'simulation failed' fitness for each objective
        for obj in self.objectives:
            obj['infinity'] = -obj['weight'] * float('inf')
        self._setup_logbook()

    def _objective_selector(self, obj):
        """Selector function for objectives.

        Handles finding the right output (or other item) and ensuring it's a quantity
        or plain number.

        TODO: Better docs & name!
        """
        component = obj['component'](self.base)
        collection = getattr(component, obj['collection'])
        value = get_item(collection, obj['item'])
        if hasattr(value, 'magnitude'):
            value = value.magnitude
        assert isinstance(value, numbers.Number)
        return value

    def _setup_toolbox(self):
        """Set up the DEAP toolboxes of GA component functions."""
        self.toolbox = toolbox = deap.base.Toolbox()
        toolbox.register('population', deap.tools.initRepeat, list, self.make_individual)
        toolbox.register('evaluate', self.evaluate_individual)
        toolbox.register('mate', self.crossover)
        toolbox.register('mutate', self.mutate)
        # Selection depends on whether this is single- or multi-objective
        if len(self.objectives) == 1:
            toolbox.register('select', deap.tools.selTournament, tournsize=2)
            toolbox.register('selectNewPop', deap.tools.selBest)
        else:
            toolbox.register('select', self.selTournamentNSGA2, tournsize=2)
            toolbox.register('selectNewPop', deap.tools.selNSGA2)

    def selTournamentNSGA2(self, individuals, k, tournsize):
        """Select k individuals by repeated NSGA2 tournaments.

        :param individuals: A list of individuals to select from.
        :param k: The number of individuals to select.
        :param tournsize: The number of individuals participating in each tournament.
        :returns: A list of selected individuals.
        """
        chosen = []
        for i in range(k):
            aspirants = deap.tools.selRandom(individuals, tournsize)
            chosen.extend(deap.tools.selNSGA2(aspirants, 1))
        return chosen

    def make_individual(self):
        """Create a new random individual."""
        return Individual(self)

    def evaluate_individual(self, ind):
        """Determine the fitness of the given individual.

        :return: a tuple of fitness values, length equal to the number of objectives
        """
        print('.', end='')
        # Set facility parameters according to this individual's genome
        ind.apply_to_facility()
        assert ind.is_valid()  # Sanity check
        ind.error = None
        # Run the model, treating failure as an infinitely bad fitness
        try:
            self.base.run()
            result = tuple(self._objective_selector(obj) for obj in self.objectives)
        except SoftTimeLimitExceeded as e:
            ind.error = e
            raise
        except Exception as e:
            ind.error = e
            result = tuple(obj['infinity'] for obj in self.objectives)
        return result

    def crossover(self, ind1, ind2):
        """Perform genetic crossover between 2 individuals."""
        if self.debug:
            print('Mate {} & {}'.format(ind1, ind2))
        gene_prob = self.parameters['geneCrossoverProbability']
        for var1, var2 in zip(ind1.variables, ind2.variables):
            if random.random() < gene_prob:
                var1.value, var2.value = var2.value, var1.value
        # Re-draw any variables that were invalidated by swaps
        ind1.repair()
        ind2.repair()
        if self.debug:
            print('  -> {} & {}'.format(ind1, ind2))

    def mutate(self, ind):
        """Mutate the genome of a single individual."""
        if self.debug:
            print('Mutate {}'.format(ind))
        gene_prob = self.parameters['mutationRate'] / len(ind.variables)
        ind.apply_to_facility()
        for var in ind.variables:
            if random.random() < gene_prob:
                var.draw()
        # Re-draw any variables that were invalidated by mutations
        ind.repair()
        if self.debug:
            print('    -> {}'.format(ind))

    def _setup_logbook(self):
        """Prepare a log keeping track of statistics during the GA execution."""
        # Record statistics of fitness
        stats_fit = deap.tools.Statistics(key=lambda ind: ind.fitness.values)
        # We keep the fitness statistics for all objectives in a single array
        stats_fit.register("min", np.min, axis=0)
        stats_fit.register("max", np.max, axis=0)
        stats_fit.register("avg", np.mean, axis=0)
        stats_fit.register("std", np.std, axis=0, ddof=1)  # is ddof required?
        self.all_stats["fit"] = stats_fit
        # Track each of the specified variables
        dummy_ind = self.make_individual()  # required to retrieve variables
        for var in dummy_ind.variables:
            if var.track:
                self._track_variable(var)
        # Create the logbook to track the evolution of the stats
        self.logbook = deap.tools.Logbook()
        self.stats = deap.tools.MultiStatistics(**self.all_stats)

    def _track_variable(self, var):
        """Set up the statistics object for tracking a variable's evolution."""
        tracking_mode = var.track
        if tracking_mode not in Tracking:
            if self.debug:
                print("Could not understand tracking option", tracking_mode)
            return
        stats = deap.tools.Statistics(key=_var_value(var.component.name,
                                                     var.item))
        # NumPy does not like arrays of quantities. Instead, we can use
        # container quantities, which encompass multiple values with the same
        # unit. This involves some conversion, unless we are sure that the units
        # will be the same across all individuals. One option is to convert to
        # base units:
        # stats_fit.register("min", lambda x: np.min([y.to_base_units().magnitude for y in x]))
        # However, this leaves dimensionless numbers. Alternatively, we can
        # convert everything to the first individual's units:
        # stats_fit.register("min", lambda y: np.min([x.to(y[0].units).magnitude for x in y] * y[0].units))
        # Or a bit more elegantly:
        if tracking_mode is Tracking.numerical:
            stats.register("min", with_units(np.min))
            stats.register("max", with_units(np.max))
            stats.register("avg", with_units(np.mean))
            stats.register("std", with_units(np.std), ddof=1)
        elif tracking_mode is Tracking.discrete:
            stats.register("count", _count)
        self.all_stats[var.name] = stats


def _var_value(component_name, item):
    """Retrieve the value of a variable from an individual."""
    return lambda ind: ind.get_variable(component_name, item).value


def _count(values):
    """Return a dictionary mapping a list's distinct values to their counts."""
    # HACK Wrap the dictionary in a list, otherwise it will be unwrapped by
    # compile() and will cause problems if the keys are not strings (eg boolean)
    return [dict(zip(*np.unique(values, return_counts=True)))]


class Tracking(Enum):
    """Whether a variable should be tracked as a numerical or discrete value."""
    numerical = 0
    discrete = 1
