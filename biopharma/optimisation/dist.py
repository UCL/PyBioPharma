from numpy.random import uniform, normal, triangular


class DistributionGenerator(object):
    """A class for generating values from a distribution."""

    def draw(self):
        """Generate a value from the distribution."""
        raise NotImplementedError


class Uniform(DistributionGenerator):
    """A generator of values from a uniform distribution over an interval."""

    def __init__(self, min_value, max_value):
        """Create a uniform generator for the given interval.

        :param domain: a list [min, max] with the range of values allowed for
                this variable.
        """
        assert min_value < max_value
        assert hasattr(min_value, "units")
        self.units = min_value.units
        self.min = min_value.magnitude
        self.max = max_value.to(self.units).magnitude

    def draw(self):
        val = uniform(self.min, self.max)
        return val * self.units


class Gaussian(DistributionGenerator):
    """A generator of normally-distributed values."""
    def __init__(self, mean, std):
        """Create a Gaussian generator with a given mean and standard deviation.

        :param mean: the mean of the variable's values' distribution.
        :param std: the standard deviation of the variable's values' distribution.
        """
        assert hasattr(mean, "units") and hasattr(std, "units")
        self.units = mean.units
        self.mean = mean.magnitude
        self.std = std.to(self.units).magnitude

    def draw(self):
        val = normal(self.mean, self.std)
        return val * self.units


class Triangular(DistributionGenerator):
    """A generator of values from a symmetrical triangular distribution."""

    def __init__(self, min_value, max_value):
        """Create a triangular generator over the given interval.

        :param domain: a list [min, max] with the range of values allowed for
                this variable.
        """
        assert min_value < max_value
        assert hasattr(min_value, "units")
        self.units = min_value.units
        self.min = min_value.magnitude
        self.max = max_value.to(self.units).magnitude
        self.mode = (self.min + self.max) / 2

    def draw(self):
        val = triangular(self.min, self.mode, self.max)
        return val * self.units
