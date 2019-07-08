
import biopharma as bp


class Product(bp.ModelComponent):
    """A Product being produced by a bio-pharma facility.

    This class encapsulates product-level parameters.
    """

    PARAMETERS = {}

    OUTPUTS = {}

    def __init__(self, facility, steps=[], sequence=None, **kwargs):
        """Initialise a new product to be manufactured in the given facility.

        :param facility: the facility that will manufacture this product
        :param steps: the ProcessStep instances required to product this product
        :param sequence: instead of specifying steps, a ProcessSequence may be given explicitly
        :param kwargs: further keyword arguments are passed to ModelComponent.__init__, notably
            name and param_filename.
        """
        super(Product, self).__init__(**kwargs)
        self.facility = facility
        facility.products.append(self)
        if sequence is not None:
            self.sequence = sequence
        elif steps:
            self.sequence = bp.ProcessSequence(steps, facility=facility, product=self)
        else:
            self.sequence = None  # This path should only be followed by tests!

    def load_parameters(self):
        """Load parameters not just for the product itself but for all model components."""
        super(Product, self).load_parameters()
        if self.sequence:
            self.sequence.load_parameters()

    def extract_outputs(self, collection='outputs'):
        """Extract this product's outputs (and those of all components) as a plain dictionary.

        :param collection: the name of the collection to extract, e.g. to select parameters instead
        """
        outputs = super(Product, self).extract_outputs(collection=collection)
        outputs['sequence'] = self.sequence.extract_outputs(collection=collection)
        return outputs

    def evaluate(self):
        """Evaluate production of this product.

        This is the main method called by the Facility to model product production.
        It estimates how long production will take, runs the process sequence associated with
        this product, and then checks whether the final solution meets requirements in terms
        of amount produced and HCP purity.
        """
        # Set inputs for our process sequence and run it
        for name, spec in self.sequence.INPUTS.items():
            self.sequence.inputs[name] = spec.zero
        self.sequence.run()
