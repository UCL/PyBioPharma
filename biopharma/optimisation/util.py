from collections import Iterable

import numpy as np


def get_item(collection, item_path):
    """Retrieve an item from a component's collection, possibly going through
    multiple levels of nesting.

    :param collection: the collection where the item resides.
    :param item_path: a string with the name of the item, or an iterable of
        strings giving its location in a nested hierarchy.
    :returns: the value of the specified item in the collection.
    """
    if isinstance(item_path, str):
        return collection[item_path]
    else:
        assert isinstance(item_path, Iterable)
        # iterate through the parts of the path until we reach the final level
        current = collection
        for item in item_path:
            current = current[item]
        return current


def with_units(func):
    """Wrap a NumPy function so that it can be run on iterables of quantities."""
    def aux(values, *args, **kwargs):
        try:
            return func([v.to(values[0].units).magnitude for v in values] *
                        values[0].units, *args, **kwargs)
        except AttributeError:  # in case of non-quantity (eg boolean) value
            return np.nan
    return aux
