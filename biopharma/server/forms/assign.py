
"""Routines for processing form input."""


def assign_parameters(form_data, optimiser):
    """Set model parameters based on values submitted in the given form.

    Also sets optimisation options such as which variables to optimise.

    :param form_data: the submitted HTML form data giving parameter values, etc.
    :param optimiser: the Optimiser instance
    """
    from .utils import field_name
    # Parameters for each model component
    options = form_data['opt_form']
    assign_component_parameters(optimiser, options)
    facility = optimiser.facility
    product = facility.products[0]
    sequence = product.sequence
    for component in [facility, product]:
        assign_component_parameters(component, form_data[field_name(component)])
    # Reorder process sequence if requested
    sequence = assign_process_sequence(optimiser, form_data['sequence_form'])
    for step in sequence.steps:
        assign_component_parameters(step, form_data['steps_form'][field_name(step)])
    # Overall optimisation settings (objectives & variables)
    from ... import optimisation as opt
    default_options = [
        # (field name in form, item name in product, minimise?)
        ('obj_min_A', 'varA', True),
        ('obj_min_B', 'varB', True),
        ('obj_max_C', 'varC', False)
    ]
    # How the objectives are defined depends on whether we are also doing
    # sensitivity analysis, i.e. if the "minimise variance" box is selected
    sensitivity = options['obj_min_sigma_varA']
    component_selector = opt.sel.product(0) if not sensitivity else opt.sel.self()
    for field, item, should_minimise in default_options:
        item_selector = item if not sensitivity else (item, 'avg')
        if options[field]:
            if sensitivity:
                # Add the target as an output of the analysis, to compute stats
                optimiser.base.add_output(
                    item, component=opt.sel.product(0), item=item)
            # Add the objective to the optimiser
            obj_desc = {"component": component_selector,
                        "item": item_selector,
                        "minimise" if should_minimise else "maximise": True}
            optimiser.add_objective(**obj_desc)
    # Add the chosen variables to the optimiser
    if options['var_bool_param']:
        optimiser.add_variable(
            gen=opt.gen.Binary(), component=opt.sel.step('test_step'), item='bool_param')
    if options['var_int_param']:
        optimiser.add_variable(gen=opt.gen.RangeGenerator(0, 10),
                               component=opt.sel.step('test_step'), item='int_param')
    # Set up the sensitivity analyser, if required
    if sensitivity:
        assign_analyser(optimiser)
    else:
        optimiser.base = optimiser.facility


def assign_component_parameters(component, defaults):
    """Set new default parameters for this component.

    This method specifies these as overrides for the parameters loaded from file, so they will
    persist as new defaults for the optimiser.

    :param component: the model component whose parameters to set
    :param defaults: a dictionary of parameter values
    """
    # The overrides dictionary has keys in the form (collection, item_name)
    # so we must specify that we want to override the component's parameters
    # (rather than its inputs or outputs)
    options = {("parameters", param): value for param, value in defaults.items()}
    component.overrides.update(options)
    component.apply_overrides()


def assign_process_sequence(optimiser, form_data):
    product = optimiser.facility.products[0]
    avail_steps = product.sequence.steps
    num_steps = len(avail_steps)
    new_steps = []
    for index in form_data['steps']:
        if index < num_steps:
            new_steps.append(avail_steps[index])
    from ...process_sequence import ProcessSequence
    product.sequence = ProcessSequence(new_steps, product=product)
    return product.sequence


def assign_analyser(optimiser):
    from ... import optimisation as opt
    analyser = optimiser.base
    # Configure the analysis with default values
    analyser.parameters['numberOfSamples'] = 4
    param = analyser.facility.products[0].parameters['param']
    width = 0.4 * param.units
    analyser.add_variable(
        gen=opt.dist.Triangular(param - width, param + width),
        component=opt.sel.product(), item='param')
    # Add the optimisation target
    if 'cogs' not in analyser.outputs:  # if CoG is not a target directly
        analyser.add_output('cogs', component=opt.sel.product(0), item='cogs')
    optimiser.add_objective(
        component=opt.sel.self(), item=('cogs', 'var'), minimise=True)
