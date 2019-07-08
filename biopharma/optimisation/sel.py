"""Convenience functions for selecting model components and their attributes."""


def facility():
    """Return a selector function for the facility a component refers to."""
    # This works both for analysis components, and facilities (in which case the
    # facility itself is returned).
    return lambda component: component.facility


def self():
    """Return a selector function that selects the component itself."""
    return lambda component: component


def step(name, product_index=0):
    """Return a selector function for the process step with the given name.

    :param name: the name of the process step to select
    :param product_index: which product's steps to look in
    """
    return lambda facility: facility.products[product_index].sequence.findStep(name)


def product(product_index=0):
    """Return a selector function for a particular product.

    :param product_index: the index of the desired product in the facility's list
    """
    return lambda facility: facility.products[product_index]


def output(output_name, product_index=0):
    """Return a selector function for a specified output of a product.

    :param output_name: the name of the output to select
    :param product_index: which product's outputs to look in
    """
    return lambda facility: facility.products[product_index].outputs[output_name]


def content(component, item, collection="outputs", strip_units=False):
    """Return a selector function for a particular item of a component.

    :param component: a selector function for the component of interest
    :param item: the name of the item to be selected
    :param collection: the name of the collection to look in
    :param strip_units: whether to remove the units (if any) of the value found
    """
    # TODO assert that the resulting value is a Number (if stripping units)
    def get_item(facility):
        component_instance = component(facility)
        collection_instance = getattr(component_instance, collection)
        value = collection_instance[item]
        if hasattr(value, 'magnitude') and strip_units:
            value = value.magnitude
    return get_item
