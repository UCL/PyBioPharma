
"""Forms for parameterising pandas DataFrames, i.e. tabular data."""

import enum

from wtforms.fields import (
    BooleanField,
    FieldList,
    FloatField,
    FormField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)

from ... import specs
from .utils import NestedForm, prettify_camel_case


def fill_table_form(form_class, column_info):
    """Assign fields to a child form for parameterising a row of a table.

    :param form_class: the FlaskForm subclass that will represent a row of parameters
    :param column_info: dictionary as returned by specs.Table.column_info, mapping
        column names to (type, label, description) tuples
    """
    for col_name, col_info in column_info.items():
        col_type, col_label, col_desc = col_info
        kwargs = {
            'label': prettify_camel_case(col_label),
            'description': col_desc,
            # 'validators': [v.InputRequired()]
        }
        if col_type == 'index':
            field_class = HiddenField
        elif col_type is float:
            field_class = FloatField
        elif col_type is int:
            field_class = IntegerField
        elif col_type is str:
            field_class = StringField
        elif col_type is bool:
            field_class = BooleanField
            kwargs['validators'] = []
        elif isinstance(col_type, enum.EnumMeta):
            field_class = SelectField
            kwargs['choices'] = [(i.name, i.name) for i in col_type]
        else:
            raise ValueError('Unexpected table column type "{}"'.format(col_type))
        setattr(form_class, col_name, field_class(**kwargs))


def make_table_form(spec, defaults):
    """Make a form for providing parameters to the given Table specification.

    The form instance will also have a method `fill_defaults` which, when called, will
    add entries for all the default values given in `defaults`.

    :param spec: the Table specification
    :param defaults: a pandas DataFrame giving default values for the table
    :returns: the form class for the full table entry
    """
    assert isinstance(spec, specs.Table)

    class RowForm(NestedForm):
        """Form for parameterising a row of {}.""".format(spec.description)

    fill_table_form(RowForm, spec.column_info)

    class TableForm(NestedForm):
        """Form for parameterising the table {}.""".format(spec.description)
        rows = FieldList(FormField(RowForm))

        def fill_defaults(self):
            """Fill in default values for all rows of the table, if none have been submitted."""
            if len(self.rows):
                return
            for row in defaults.to_dict(orient='records'):
                entry = RowForm()
                for key, value in row.items():
                    if hasattr(value, 'magnitude'):
                        if entry[key].type == 'StringField':
                            value = str(value.units)
                        else:
                            value = value.magnitude
                    setattr(entry, key, value)
                self.rows.append_entry(entry)

    return TableForm
