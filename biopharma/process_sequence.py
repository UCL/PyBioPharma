
import numpy as np

import biopharma as bp


class ProcessSequence(bp.ModelComponent):
    """Chain a sequence of ProcessStep instances into a full process.

    This handles passing the outputs of one step to the inputs of the next,
    and providing access to the overall inputs and outputs of the process.
    """

    def __init__(self, steps, facility=None, product=None):
        """Create a new process.

        :param steps: the ProcessStep instances making up this process
        :param facility: the Facility this process is run within.
            If not given, will be determined from the first step.
        :param product: the Product being manufactured by this process
        """
        assert len(steps) > 0, "You cannot have an empty process"
        self.steps = steps
        self.name = self.__class__.__name__
        # Set process i/o on the basis of first/last steps
        self.INPUTS = steps[0].INPUTS
        self.inputs = steps[0].inputs
        output_specs = steps[-1].OUTPUTS.copy()
        self.OUTPUTS = output_specs
        self.outputs = bp.SpecifiedDict(output_specs, 'output', component=self)
        # Set facility & product here and on steps depending on where they were first set
        if facility:
            self.facility = facility
            for step in steps:
                step.facility = facility
        else:
            self.facility = steps[0].facility
        if product:
            self.product = product
            for step in steps:
                step.product = product

    def load_parameters(self):
        """Load the parameters for each process step."""
        for step in self.steps:
            step.load_parameters()

    def extract_outputs(self, collection='outputs'):
        """Extract this facility's outputs (and those of all components) as a plain dictionary.

        :param collection: the name of the collection to extract, e.g. to select parameters instead
        """
        outputs = super(ProcessSequence, self).extract_outputs(collection=collection)
        outputs['steps'] = []
        for step in self.steps:
            outputs['steps'].append(step.extract_outputs(collection=collection))
        return outputs

    def run(self):
        """Run this process."""
        # Run each individual process step
        for i, step in enumerate(self.steps):
            if i > 0:
                prev_step = self.steps[i - 1]
                for name in step.INPUTS.keys():
                    step.inputs[name] = prev_step.outputs[name]
            step.run()
        # Copy final step outputs to our dictionary
        for name, value in self.steps[-1].outputs.items():
            self.outputs[name] = value

    def findStep(self, name):
        """Find a particular step within this sequence.

        :param name: the name of the step to look for, which will be matched against the name
            attribute of each step (which can be set in the step's constructor).
        """
        for step in self.steps:
            if step.name == name:
                return step
        raise ValueError(
            'Process step "{}" not found within this ProcessSequence.'
            ' Do you need to provide a "name={}" argument when creating a step?'.format(
                name, name))

    def step_outputs(self, item):
        """Get the 'item' output from each step as an array with units.

        :param item: the name of the output to extract from each step
        :returns: a numpy array containing that output for each step in order
        """
        values = [step.outputs[item] for step in self.steps]
        return np.array([value.to_base_units().magnitude
                         for value in values]) * values[0].to_base_units().units

    def step_increments(self, item):
        """Get the change in 'item' between inputs & outputs from each step.

        :param item: the name of the input/output to extract from each step
        :returns: a numpy array containing how much that item has changed between input and output
            for each step in order
        """
        values = [step.outputs[item] - step.inputs[item] for step in self.steps]
        return np.array([value.to_base_units().magnitude
                         for value in values]) * values[0].to_base_units().units
