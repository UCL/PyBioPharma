
import os

import biopharma as bp


class Facility(bp.ModelComponent):
    """A bioprocessing facility.

    This class handles the overall loading of parameters and running production pipelines.

    Pure utility methods which do not depend on parameter values go in the bp.util module.
    """

    # Overall facility inputs
    INPUTS = {}
    # Overall facility outputs
    OUTPUTS = {}
    # Facility-level parameters
    PARAMETERS = {}

    def __init__(self, data_path, **kwargs):
        """Create a new facility.

        :param data_path: folder containing parameter files and other facility configuration
            information
        """
        assert os.path.isdir(data_path)
        self.data_path = data_path
        self.facility = self  # Because ModelComponent accesses self.facility.data_path!
        super(Facility, self).__init__(**kwargs)
        self.products = []

    def run(self):
        """Run the process economics model for this facility.

        This is the main entry point for simulating production of the products specified in
        self.products.
        """
        # Evaluate the cost of producing each product
        for product in self.products:
            product.evaluate()

    def load_parameters(self):
        """Load parameters not just for the facility itself but for all model components."""
        super(Facility, self).load_parameters()  # Load our parameters
        for product in self.products:
            product.load_parameters()

    def extract_outputs(self, collection='outputs'):
        """Extract this facility's outputs (and those of all components) as a plain dictionary.

        :param collection: the name of the collection to extract, e.g. to select parameters instead
        """
        outputs = super(Facility, self).extract_outputs(collection=collection)
        outputs['products'] = []
        for product in self.products:
            outputs['products'].append(product.extract_outputs(collection=collection))
        return outputs
