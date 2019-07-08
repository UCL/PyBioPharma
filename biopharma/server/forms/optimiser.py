
"""Forms for parameterising the optimiser."""

from flask_wtf import FlaskForm
from wtforms.fields import (
    BooleanField,
    FieldList,
    FormField,
    SelectField,
    StringField,
)
from wtforms.validators import ValidationError, Length
from wtforms.widgets import ListWidget

from .utils import field_name, make_component_form, NestedForm


def make_all_forms(optimiser):
    """Build a set of forms for specifying an optimisation.

    Rather than declaring a form declaratively, we need to create one programmatically,
    with a sub-form for each model component, as well as one for the main optimiser
    settings.

    :param optimiser: the optimiser instance
    :returns: an instantiated form
    """

    facility = optimiser.facility
    product = facility.products[0]
    steps = product.sequence.steps

    class OptimisationForm(FlaskForm):
        """Main form for setting up an optimisation."""
        opt_form = FormField(make_optimiser_form(optimiser), label='Optimiser')
        sequence_form = FormField(make_sequence_form(optimiser), label='Process sequence')
        steps_form = FormField(make_steps_forms(steps), label='Unit operations')
        name_field = StringField('Name', [Length(max=50)])

    for component in [facility, product]:
        setattr(
            OptimisationForm,
            field_name(component),
            FormField(make_component_form(component), label=component.name))
    form = OptimisationForm()

    # Fill in default values for table forms
    def fill_defaults(form):
        if hasattr(form, 'fill_defaults'):
            form.fill_defaults()
        else:
            for field in form:
                if field.type == 'FormField':
                    fill_defaults(field)
    fill_defaults(form)

    # Add a form attribute on each component giving the corresponding instantiated form.
    # This is used in the Jinja templates.
    for component in [facility, product]:
        component.form = form[field_name(component)]
    for step in product.sequence.steps:
        step.form = form['steps_form'][field_name(step)]
    optimiser.form = form['opt_form']

    return form


def make_optimiser_form(optimiser):
    """Make a child form for the optimisation settings.

    :param optimiser: the Optimiser instance
    :returns: a subclass of FlaskForm; NB not an instance!
    """
    # This sets up the initial form with the optimiser's parameters
    OptimiserForm = make_component_form(optimiser)
    # Now add options for specifying objectives
    OptimiserForm.obj_min_A = BooleanField('Minimise A', default=True)
    OptimiserForm.obj_min_sigma_varA = BooleanField('Minimise variance in A')
    OptimiserForm.obj_min_B = BooleanField('Minimise B')
    OptimiserForm.obj_max_C = BooleanField('Maximise C')
    # Options saying which variables to optimise
    OptimiserForm.var_bool_param = BooleanField(
        'Optimise the choice of a binary option',
        default=True)
    OptimiserForm.var_int_param = BooleanField('Optimise the range of an integer',
                                               default=True)
    return OptimiserForm


def make_sequence_form(optimiser):
    """Make a child form for selecting the process sequence.

    The default model provides the list of available steps. This form gives a drop-down
    menu for each step, defaulting to the same as the default model, but with all options
    available. It also provides a 'None' option for each slot. The validation checks that
    a given step isn't used more than once.

    :param optimiser: the Optimiser instance
    :returns: a subclass of FlaskForm; NB not an instance!
    """
    default_sequence = optimiser.facility.products[0].sequence
    step_names = [step.name for step in default_sequence.steps]
    step_names.append('None')
    step_field = SelectField(
        label='',  # No label
        choices=[(i, step) for i, step in enumerate(step_names)],
        coerce=int)
    num_entries = len(default_sequence.steps)

    class SequenceForm(NestedForm):
        """Form for defining the sequence of process steps."""
        steps = FieldList(step_field,
                          min_entries=num_entries,
                          max_entries=num_entries,
                          default=tuple(range(num_entries)),
                          widget=ListWidget(html_tag='ol'))

        def validate_steps(form, field):
            """Check that each step is distinct."""
            if len(set(field.data)) != len(field.data):
                raise ValidationError('Each step in the process must be distinct')

    return SequenceForm


def make_steps_forms(steps):
    """Make a set of forms for configuring individual process steps.

    :param steps: list of ProcessStep instances to configure
    :returns: the form class for defining the steps' parameters
    """
    class ProcessStepForms(NestedForm):
        """Form containing parameter forms for each process step."""

    for step in steps:
        setattr(
            ProcessStepForms,
            field_name(step),
            FormField(make_component_form(step), label=step.name))
    return ProcessStepForms
