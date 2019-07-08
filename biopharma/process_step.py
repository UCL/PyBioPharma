
import biopharma as bp
from .specs import Q, Computed


class ProcessStep(bp.ModelComponent):
    """Base class for process steps.

    This class defines the interface for steps in the process to create a single
    product. It also defines parameters, inputs and outputs common to all such
    steps.

    The INPUTS, OUTPUTS and PARAMETERS class members are specifications, saying
    what this model component expects as inputs etc. Subclasses may also specify
    their own INPUTS etc. which are added to those given here. For each entry,
    we specify the name of the variable, its units or type, and give a description
    explaining its purpose.
    """

    INPUTS = {
        'mass': Q('g', 'Total mass before this step'),
        'volume': Q('L', 'Volume before this step'),
        'water': Q('L', 'Amount of water used'),
    }

    OUTPUTS = {
        'mass': Q('g', 'Total mass remaining after this step'),
        'volume': Q('L', 'Volume remaining after this step'),
        'water': Q('L', 'Amount of water used'),
    }

    PARAMETERS = {
        'effectiveYield': Computed(
            lambda self: self.parameters['yield'],
            'The effective yield of this process step; defaults to match a "yield" parameter but'
            ' can be overridden by specific step classes.'),
    }

    def __init__(self, facility=None, product=None, **kwargs):
        """Constructor for an individual process step.

        :param facility: the facility this step is run within.
            If not given, will be determined when this step is associated with a ProcessSequence.
        :param product: the product this step is helping to produce.
            If not given, will be determined when this step is associated with a ProcessSequence.
        :param kwargs: further keyword arguments are passed to ModelComponent.__init__, notably
            name and param_filename.
        """
        super(ProcessStep, self).__init__(**kwargs)
        self.facility = facility
        self.product = product

    def run(self):
        """Perform all parts of this process step, including time and cost calculations.

        This method is designed to be called by external code, and itself calls the
        individual methods implemented by subclasses.

        TODO: Perhaps have a class member PASS_THROUGH that says which inputs just get copied
        straight to outputs, and implement that logic here, rather than making it 'magic'?
        """
        self.mass_balance()
        self.calculate_time()
        self.calculate_cost()

    def mass_balance(self):
        """Perform the biochemistry of this process step.

        Called before calculate_time and calculate_cost.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def calculate_time(self):
        """Calculate how long this process step would take to run in the facility.

        Called after mass_balance and before calculate_cost.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def calculate_cost(self):
        """Calculate the cost of running this process step in the facility.

        Called after mass_balance and calculate_time.

        Must be implemented by subclasses.
        """
        raise NotImplementedError
