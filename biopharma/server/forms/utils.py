
"""Common utilities for BioPharma web forms."""

import numbers
import re

from flask_wtf import FlaskForm
from wtforms.fields import (
    BooleanField,
    FloatField,
    FormField,
    SelectField,
)
import wtforms.validators as v

from ... import specs


class NestedForm(FlaskForm):
    """Base class for nested forms, which don't need their own CSRF."""
    class Meta:
        csrf = False


def field_name(component):
    """Return the name for the FormField built for the given component."""
    return 'comp-' + component.name


def make_component_form(component):
    """Make a (child) form for parameterising a single model component.

    :param component: the component whose parameters should be editable.
    :returns: a subclass of FlaskForm; NB not an instance!
    """
    return _make_child_form('the parameters of component ' + component.name,
                            component.PARAMETERS,
                            component.parameters)


_CAMEL_CASE_RE = re.compile(r"""
    (
        (?<=[a-z])       # group is preceded by a lower char
        [A-Z]{2,}        # 2 or more upper chars
        (?=[a-z])        # group is followed by a lower char or _
        |                # or
        \A               # start of string
        [A-Z]{2,}        # 2 or more upper chars
        (?=[a-z])        # group is followed by a lower char
        |                # or
        (?<=[a-z])       # group is preceded by a lower char
        [A-Z]            # a single upper char
        [a-z]+           # one or more lower chars
    )""", flags=re.VERBOSE)


def prettify_camel_case(name):
    """Convert a camelCase parameter name to something nicer for display.

    We split it into space-separated words, with just the first capitalised.
    This method also handles cases like:
    - numberOfABCruns -> Number of ABC runs
    - FTgain -> FT gain

    :param name: the (parameter) name to convert
    """
    words = [word if word.isupper() else word.lower()
             for word in _CAMEL_CASE_RE.split(name)]
    pretty = ' '.join(words)
    pretty = pretty[0].upper() + pretty[1:]
    pretty = pretty.replace(' s_', 's ').replace('_', ' ').replace('  ', ' ')
    return pretty


def _make_child_form(title, specifications, defaults):
    """Make a child form for a group of parameters.

    This is used both for components and for nested specifications.

    :param title: used to construct a docstring for the form
    :param specifications: dictionary of specifications for these parameters
    :param defaults: dictionary of default values for these parameters
    """
    class ChildForm(NestedForm):
        """Form for {}.""".format(title)

    for param, spec in specifications.items():
        kwargs = {
            'description': spec.description,
            'label': prettify_camel_case(param)
        }
        field_type = _spec_field_type(param, spec, kwargs, defaults)
        if field_type is not None:
            if isinstance(spec, specs.Q):
                default = lambda q: q.magnitude  # noqa
            else:
                default = lambda v: v  # noqa
            if param in defaults and not spec.nested:
                kwargs['default'] = default(defaults[param])
                if field_type not in [BooleanField, FormField]:
                    kwargs['validators'] = [v.InputRequired()]
            setattr(ChildForm, param, field_type(**kwargs))
    return ChildForm


def _spec_field_type(param, spec, kwargs, defaults):
    """Determine what input field is suitable for the given specification (if any).

    Returns either a field class or None, if nothing is suitable.

    :param param: the name of the parameter this field is for
    :param spec: the specification needing an input field
    :param kwargs: will be filled in with any extra keyword arguments this field will need
    :param defaults: the default values for the collection this field is part of
    """
    if spec.hidden:
        return None
    field_class = None
    if isinstance(spec, specs.Q):
        field_class = FloatField
        kwargs['label'] += ' ({:H})'.format(spec.units)
    elif isinstance(spec, specs.Value):
        if spec.type is bool:
            field_class = BooleanField
        elif issubclass(spec.type, numbers.Number):
            field_class = FloatField
    elif isinstance(spec, specs.Enumerated):
        field_class = SelectField
        kwargs['choices'] = [(i.name, prettify_camel_case(i.name)) for i in spec.enum]
    elif isinstance(spec, specs.Nested):
        kwargs['form_class'] = _make_child_form(
            'parameters nested under ' + param,
            spec.nested,
            defaults.get(param, {}))
        field_class = FormField
    elif isinstance(spec, specs.Table):
        from .tables import make_table_form
        kwargs['form_class'] = make_table_form(spec, defaults[param])
        field_class = FormField
    return field_class
