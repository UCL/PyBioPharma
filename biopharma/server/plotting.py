"""Functions for generating the plots displayed in the web interface."""

from bokeh.core.properties import value
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.palettes import viridis
from bokeh.plotting import figure

import biopharma as bp


def make_cost_plot(optimiser):
    """A bar chart showing the cost breakdown for the best individual."""
    # TODO We might want to call this function on the individual rather than the
    # optimiser, or to allow to plot results for multiple individuals at a time.

    # Rerun facility for best solution
    best = optimiser.outputs['bestIndividuals'][0]
    if best.error:
        return '', ''
    best.apply_to_facility()
    try:  # the best solution might still produce errors!
        optimiser.facility.run()
    except Exception:
        return '', ''

    # Cost breakdown data
    product = optimiser.facility.products[0]
    y_units = bp.units.GBP / bp.units.g
    grams_produced = product.outputs['grams_produced'].to('g')
    # Choose which cost aspects to plot:
    # - the fields where they are found in the product outputs
    cost_fields = ['cost_1', 'cost_2', 'cost_3']
    # - the names under which they will be displayed
    cost_source_names = ['Cost 1', 'Cost 2', 'Cost 3']
    # TODO It would be nice to connect the field and display names somehow, so
    # a source is only declared once
    all_costs = [(product.outputs[cost_source] / grams_produced).magnitude
                 for cost_source in cost_fields]

    inds = ['Best Solution']  # we are only plotting one bar
    data = {'inds': inds}  # putting the data in the form Bokeh wants...
    data.update(zip(cost_source_names, [[cost] for cost in all_costs]))
    source = ColumnDataSource(data=data)

    p = figure(x_range=inds)
    p.vbar_stack(cost_source_names, x='inds', width=0.2, source=source,
                 color=viridis(len(cost_source_names)),
                 legend=[value(x) for x in cost_source_names])

    p.y_range.start = 0
    p.yaxis.axis_label = 'Cost of goods ({})'.format(y_units)
    p.xgrid.grid_line_color = None
    p.xaxis.major_label_text_color = None  # remove tick label
    p.outline_line_color = None  # no border
    p.legend.location = "top_right"

    return components(p)


def make_sample_scatter_plot(optimiser):
    """A sample scatter plot."""
    best = optimiser.outputs['bestIndividuals'][0]
    step_names = ['stepA', 'stepB', 'stepC']
    colours = viridis(len(step_names))
    p = figure()
    for (i, name) in enumerate(step_names):
        x = best.get_variable(name, 'varA').value
        y = best.get_variable(name, 'varB').value
        p.circle(x.magnitude, y.magnitude, size=20, color=colours[i],
                 legend=name)
    # All steps should have the same units as they follow the same output spec?
    p.xaxis.axis_label = 'Variable A ({})'.format(x.units)
    p.yaxis.axis_label = 'Variable B ({})'.format(y.units)
    p.legend.location = 'center'

    return components(p)
