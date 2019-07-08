import numpy as np
from numpy.testing import assert_allclose
import pytest

from biopharma import units
import biopharma.optimisation as opt
from biopharma.optimisation.util import with_units


@pytest.fixture(autouse=True)
def wrap_numpy_with_units(monkeypatch):
    """Make it so we don't need to explicitly wrap NumPy calls for units."""
    for method in ['min', 'max', 'mean', 'var']:
        monkeypatch.setattr(np, method, with_units(getattr(np, method)))


def test_uniform_distribution():
    """Check that the uniform generator samples resemble the distribution."""
    n_samples = 10000
    limit = 5 * units("m")
    gen = opt.dist.Uniform(-limit, limit)
    true_avg = 0 * units("m")
    true_var = limit * limit / 3
    samples = [gen.draw() for i in range(n_samples)]
    check_samples_match(samples,
                        min=-limit, max=limit, avg=true_avg, var=true_var,
                        rtol=0.05, atol=0.1)


def test_triangular_distribution():
    """Check that the triangular generator samples resemble the distribution."""
    n_samples = 10000
    min = 1 * units("m")
    max = 5 * units("m")
    gen = opt.dist.Triangular(min, max)
    true_avg = (min + max) / 2
    # Variance of triangular distribution with (min, max, mode) = (a, b, c) is:
    # (a^2 + b^2 + c^2 - a*b - a*c -b*c) / 18
    # which for symmetric distributions reduces to:
    true_var = (min - max) ** 2 / 24
    samples = [gen.draw() for i in range(n_samples)]
    check_samples_match(samples,
                        min=min, max=max, avg=true_avg, var=true_var,
                        rtol=0.05)


def test_gaussian_distribution():
    """Check that the Gaussian generator samples resemble the distribution."""
    n_samples = 10000
    mean = 2 * units("m")
    var = 1 * units("m")
    gen = opt.dist.Gaussian(mean, var)
    samples = [gen.draw() for i in range(n_samples)]
    check_samples_match(samples, avg=mean, var=var,
                        rtol=0.05)


def check_samples_match(samples, min=None, max=None, avg=None, var=None,
                        rtol=1e-7, atol=0):
    """Ensure that the given samples are within a desired range and match the
    expected average and variance.
    """
    if min is not None:
        assert not np.min(samples) < min
    if max is not None:
        assert not np.max(samples) > max
    if avg is not None:
        assert_allclose(np.mean(samples), avg, rtol=rtol, atol=atol)
    if var is not None:
        assert_allclose(np.var(samples), var, rtol=rtol, atol=atol)
