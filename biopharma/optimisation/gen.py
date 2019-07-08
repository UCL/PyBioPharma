"""Generators for genes.

These classes provide methods for drawing new values for Variables,
and for checking that Variable values do not break any constraints
on valid Individuals.
"""

import random

import biopharma as bp

#
# First we define the generic Generator classes.
# Specific versions for particular types of parameter are at the end of the file.
#


class Generator:
    """Base class for generators, declaring the interface and some default behaviour."""

    def draw(self, var):
        """Draw a new value for the given Variable that obeys any constraints.

        :param var: the Variable instance to draw a value for
        """
        raise NotImplementedError

    def is_valid(self, var):
        """Check whether the current value of the variable meets any constraints.

        :param var: the Variable instance whose value to check
        """
        raise NotImplementedError

    def repair(self, var):
        """Alter this variable if it doesn't meet its constraints, so that it does.

        Here this means re-drawing a valid value at random, but subclasses may
        implement more intelligent routines to choose a similar value.
        """
        var.value = self.draw(var)

    def describe(self, var):
        """Return a concise description of this variable's value for reporting/debugging.

        By default just returns the value, but can be overridden by subclasses to provide
        more descriptive info.
        """
        return var.value


class RangeGenerator(Generator):
    """Base class for generators selecting from a range."""

    def __init__(self, range_min, range_max):
        """Create a new range generator.

        :param range_min: minimum inclusive allowed value
        :param range_max: maximum inclusive allowed value
        """
        self.update_range(range_min, range_max)

    def update_range(self, range_min, range_max):
        """Update the allowed range for this generator."""
        if hasattr(range_min, 'units'):
            assert range_min.units == range_max.units
            self.range_min = range_min.magnitude
            self.range_max = range_max.magnitude
            self.units = range_min.units
        else:
            self.range_min = range_min
            self.range_max = range_max
            self.units = 1

    def check_range(self, var):
        """Check that the current range is appropriate for the given variable.

        This is called before drawing a value or checking validity to make sure that the
        range is appropriate for this particular variable - other parameters may affect
        the allowed range. By default this does nothing; subclasses may call update_range
        if needed.
        """
        pass

    def draw(self, var):
        """Draw a new value within the range."""
        self.check_range(var)
        return float(self.draw_from(self.range_min, self.range_max)) * self.units

    def is_valid(self, var):
        """Check if the variable's value lies within the range."""
        self.check_range(var)
        value = var.value
        return value >= self.range_min * self.units and value <= self.range_max * self.units

    """By default we draw integers within the range."""
    draw_from = random.randint


class ChoiceGenerator(Generator):
    """Base class for generators that select from a list of choices."""

    def __init__(self, choices):
        """Create a new generator with specified selection of choices."""
        self.update_choices(choices)

    def update_choices(self, choices):
        """Update the list of values to choose from."""
        self.choices = list(choices)

    def check_choices(self, var):
        """Check whether our list of choices is appropriate for this variable.

        This is called before drawing a value or checking validity to make sure that the
        choices are appropriate for this particular variable - other parameters may affect
        the allowed selection. By default this does nothing; subclasses may call update_choices
        if needed.
        """
        pass

    def draw(self, var):
        """Draw a new value from our list of choices."""
        self.check_choices(var)
        return random.choice(self.choices)

    def is_valid(self, var):
        """Check if the variable's value is one of our choices."""
        self.check_choices(var)
        return var.value in self.choices


#
# Generators specific to particular parameters are defined below here.
#


class Binary(ChoiceGenerator):
    """Generator for choosing a boolean value."""

    def __init__(self):
        super(Binary, self).__init__([False, True])

    def draw(self, var):
        """We always flip value when asked to re-draw."""
        if var.value is None:
            return random.choice(self.choices)
        else:
            return not var.value


class ExampleDependentRange(RangeGenerator):
    """Example generator defining check_range."""

    def __init__(self):
        # The range depends on the variable, so is calculated in check_range.
        super(ExampleDependentRange, self).__init__(0, 0)

    def check_range(self, var):
        """Set the range based on the another parameter."""
        table_index = var.component.parameters['id']
        table = var.individual.optimiser.parameters['table']
        table_row = table.loc[table_index]
        self.update_range(table_row['range_min'], table_row['range_max'])
