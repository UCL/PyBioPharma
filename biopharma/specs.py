"""
These classes define the different kinds of specification that can be supplied
for inputs, outputs, and parameters within the system. They handle parsing of
values from parameter files.
"""

from .core import SpecificationViolatedError
from .units import units  # Our central units registry

import copy
import enum
import numbers
import os
import math

import numpy as np
import pandas as pd
import pint


__all__ = ['Specification',
           'Q', 'Value', 'Enumerated', 'Nested', 'Computed',
           'Table', 'in_units']


class Specification:
    """Base class for specifications."""

    def __init__(self, desc, hidden=False):
        """Create a new specification, storing its description.

        :param desc: text description of what this specification is for
        :param hidden: if set to True for a parameter specification, the parameter will not
            be editable through the web interface
        """
        self.description = desc
        self.hidden = hidden

    def clone(self):
        """Create a copy of this specification suitable for use by another model component.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def parse(self, value):
        """Parse an entry from a YAML file that should conform to this specification.

        :returns: a valid value in the correct type, if possible

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def validate(self, value):
        """Test whether a value is valid according to this specification.

        :param value: the value to test
        :returns: the value (if valid) perhaps adjusted to conform more exactly to the spec
            (e.g. in the expected units rather than just dimensionally consistent)

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def coerce(self, value):
        """Pretend a plain value is valid according to this specification, if possible.

        :param value: the value to coerce
        :returns: something like the value but valid according to this specification
        :raises: ValueError if this isn't possible
        """
        raise ValueError('Cannot coerce {} to specification {}'.format(
            value, self.__class__.__name__))

    @property
    def nested(self):
        """If this is a nested specification, return the nested spec dictionary."""
        return None

    @property
    def data_path(self):
        """The folder in which to look for CSV files referenced by Table specs."""
        return self.component.facility.data_path

    """Defined in the Computed spec to override reading a specified value."""
    get = None


class Q(Specification):
    """Specify a quantity with units."""

    def __init__(self, units_str, desc, **kwargs):
        """Create a new Quantity specification.

        :param units_str: the units that values are required to have
        :param desc: text description of this field
        :param kwargs: extra keyword arguments are passed to the base Specification class
        """
        super(Q, self).__init__(desc, **kwargs)
        self.units = units(units_str).units

    def __eq__(self, other):
        return (isinstance(other, Q) and
                self.units == other.units and self.description == other.description)

    def clone(self):
        return copy.copy(self)

    @property
    def zero(self):
        """Return a zero value matching this specification."""
        return 0 * self.units

    @property
    def inf(self):
        """Return an infinite value matching this specification."""
        return math.inf * self.units

    def parse(self, value):
        """Parse a string defining a Quantity."""
        try:
            value = units(str(value))
        except (pint.UndefinedUnitError, Exception) as e:
            raise SpecificationViolatedError(
                'Failed to parse {} as a value with units: {}'.format(
                    value, str(e)))
        return self.validate(value)

    def validate(self, value):
        """Test whether a value is valid according to this specification."""
        if isinstance(value, numbers.Number):
            if self.units.dimensionality != units.dimensionless.dimensionality:
                raise SpecificationViolatedError(
                    'Number "{}" provided but quantity with units {} required'.format(
                        value, self.units))
            value = value * self.units
        else:
            try:
                value = value.to(self.units)
            except pint.errors.DimensionalityError:
                raise SpecificationViolatedError(
                    'Value "{}" does not have units {}'.format(
                        value, self.units))
        return value

    def coerce(self, value):
        """Convert a magnitude into a quantity with the specified units."""
        if isinstance(value, numbers.Number):
            return value * self.units
        else:
            return self.validate(value)

    def with_same_units(self, desc):
        """Create a spec with the same units as this and a given description."""
        clone = self.clone()
        clone.description = desc
        return clone

    def with_squared_units(self, desc):
        """Create a spec by squaring this one's units and with the given description.

        For example, can be used for specifying the variance of a quantity with
        these units.
        """
        clone = self.clone()
        clone.units = self.units * self.units
        clone.description = desc
        return clone


class Value(Specification):
    """Specify a simple value of a basic Python type (e.g. int, bool)."""

    def __init__(self, req_type, desc, **kwargs):
        """Create a new Value specification.

        :param req_type: the type that values are required to have
        :param desc: text description of this field
        :param kwargs: extra keyword arguments are passed to the base Specification class
        """
        super(Value, self).__init__(desc, **kwargs)
        self.type = req_type

    def __eq__(self, other):
        return (isinstance(other, Value) and
                self.type is other.type and self.description == other.description)

    def clone(self):
        return copy.copy(self)

    def parse(self, value):
        """Check that value is indeed an instance of the correct type."""
        if self.type is float and isinstance(value, int):
            # Special case that's easy for users to do and shouldn't be an error
            value = float(value)
        return self.validate(value)

    def validate(self, value):
        """Check that value is indeed an instance of the correct type."""
        if not isinstance(value, self.type):
            raise SpecificationViolatedError(
                'Value "{}" is not an instance of {}'.format(
                    value, self.type))
        return value

    def coerce(self, value):
        """Try to convert the value to our specified type."""
        return self.type(value)


class Enumerated(Specification):
    """Specify a value from a particular Enum."""

    def __init__(self, enum_, desc, **kwargs):
        """Create a new Enumerated specification.

        :param enum_: the Enum from which values may be drawn
        :param desc: text description of this field
        :param kwargs: extra keyword arguments are passed to the base Specification class
        """
        super(Enumerated, self).__init__(desc, **kwargs)
        assert isinstance(enum_, enum.EnumMeta)
        self.enum = enum_

    def __eq__(self, other):
        return (isinstance(other, Enumerated) and
                self.enum is other.enum and self.description == other.description)

    def clone(self):
        return copy.copy(self)

    def parse(self, value):
        """Parse a string or value as a member of our Enum."""
        if isinstance(value, str):
            try:
                value = getattr(self.enum, value)
            except AttributeError:
                raise SpecificationViolatedError(
                    'Value "{}" is not a member of the {} enumeration'.format(
                        value, self.enum.__name__))
        else:
            try:
                value = self.enum(value)
            except ValueError:
                raise SpecificationViolatedError(
                    'Value "{}" is not a member of the {} enumeration'.format(
                        value, self.enum.__name__))
        return self.validate(value)

    def validate(self, value):
        """Check that the given value is a member of our Enum."""
        if not isinstance(value, self.enum):
            raise SpecificationViolatedError(
                'Value "{}" is not a member of the {} enumeration'.format(
                    value, self.enum.__name__))
        return value

    def coerce(self, value):
        """Try to parse the value as a member of our Enum."""
        return self.parse(value)


def in_units(name=None, col=None):
    """Helper function for Table specification to describe column units.

    Either the name or col parameter must be given, but not both.

    :param name: a string giving the units this column is assumed to be measured in
    :param col: the name of the column giving the units for this column
    """
    assert name is None or col is None, 'You cannot specify units by both name and column'
    assert not (name is None and col is None), 'A units specification must be given'
    if name is None:
        return {'col': col}
    else:
        return {'name': name}


class Table(Specification):
    """Specify a table of data read from CSV with Pandas."""

    def __init__(self, desc, columns={}, index=None, column_descs={}, **kwargs):
        """Create a table specification.

        :param desc: textual description of this field
        :param columns: dictionary mapping column names (as given in the CSV header)
            to Python types. The 'in_units' helper may be used in place of a type if the
            column represents a quantity measured in some units.
        :param index: the name of the column containing the table index
        :param column_descs: descriptions for each column. Keys should match column names
            in the columns parameter. If a description is not given for a column, the
            column name is used by default. Used to set up self.column_descriptions.
        :param kwargs: extra keyword arguments are passed to the base Specification class
        """
        super(Table, self).__init__(desc, **kwargs)
        self._columns = columns
        self._index = index
        # Figure out arguments for read_csv based on the spec
        self._dtypes = {}
        self._converters = {}
        self._units_columns = {}
        for col_name, col_spec in columns.items():
            if isinstance(col_spec, type):
                if isinstance(col_spec, enum.EnumMeta):
                    def parse_enum(val, col_spec=col_spec):
                        if isinstance(val, col_spec):
                            return val
                        try:
                            return col_spec(int(val))
                        except ValueError:
                            try:
                                return getattr(col_spec, val)
                            except AttributeError:
                                raise SpecificationViolatedError(
                                    'Cannot convert "{}" to enum {}'.format(
                                        val, col_spec.__name__))
                    self._converters[col_name] = parse_enum
                else:
                    self._dtypes[col_name] = col_spec
            elif isinstance(col_spec, dict):
                # in_units specification
                if 'name' in col_spec:
                    # Fixed units provided for whole column
                    self._converters[col_name] = self.in_units(col_spec['name'])
                elif 'col' in col_spec:
                    # Units defined in another column
                    units_col = col_spec['col']
                    self._converters[units_col] = units
                    self._dtypes[col_name] = float
                    self._units_columns[col_name] = units_col
                else:
                    raise ValueError('Invalid in_units specification for column {}: {}'.format(
                        col_name, col_spec))
            else:
                raise ValueError('Invalid column specification for column {}: {}'.format(
                    col_name, col_spec))
        self._column_names = set(columns.keys())
        self._column_names.update(self._units_columns.values())
        if index:
            self._column_names.add(index)
        # Store column descriptions, handling defaults where not specified
        self.column_descriptions = {name: name for name in columns}
        for name, desc in column_descs.items():
            if name not in columns:
                raise ValueError('Column description given for non-existent column {}'.format(
                    name))
            self.column_descriptions[name] = desc

    @property
    def column_info(self):
        """Provides info required by the web interface for editing this kind of table.

        :returns: a mapping from column name to (type, label, description) tuples.
            The index column is indicated by type = 'index'.
        """
        info = {}
        for col_name, col_spec in self._columns.items():
            desc = self.column_descriptions[col_name]
            label = col_name
            if isinstance(col_spec, type):
                info[col_name] = (col_spec, label, desc)
            else:
                assert isinstance(col_spec, dict)  # in_units specification
                if 'name' in col_spec:
                    label = '{} ({})'.format(col_name, col_spec['name'])
                    info[col_name] = (float, label, desc)
                else:
                    assert 'col' in col_spec
                    info[col_name] = (float, label, desc)
                    info[col_spec['col']] = (str, col_spec['col'], 'Units for ' + label)
        info[self._index] = ('index', self._index, self.column_descriptions[self._index])
        return info

    def clone(self):
        return copy.copy(self)

    @staticmethod
    def in_units(units_name):
        """Make a converter function for pandas.read_csv to yield a value in the given units."""
        units_obj = units(units_name)

        def converter(value):
            if hasattr(value, 'units'):
                value = value.to(units_obj)
            else:
                try:
                    value = float(value) * units_obj
                except ValueError:
                    value = units(value)
            return value
        return converter

    CSV_TAG = '&CSV::'

    def parse(self, value):
        """Parse a CSV file name by reading the contents.

        Alternatively, if value starts with the magic string '&CSV::', it is treated as actual
        CSV data. If it is already a DataFrame, it is just validated to match the spec.
        """
        if isinstance(value, pd.DataFrame):
            # Fix quantity columns, which can get loaded from YAML as strings
            def fix_units(datum):
                if hasattr(datum, 'magnitude'):
                    return datum
                elif str(datum)[:3] == 'nan':
                    return float('nan') * units.dimensionless
                else:
                    return units(datum)
            units.autoconvert_offset_to_baseunit = True  # To handle degC units
            for col_name, col_spec in self._columns.items():
                if isinstance(col_spec, dict):
                    value[col_name] = value[col_name].apply(fix_units)
            units.autoconvert_offset_to_baseunit = False
            return self.validate(value)
        if value.startswith(Table.CSV_TAG):
            from io import StringIO
            data_source = StringIO(value[6:])
        else:
            data_source = os.path.join(self.data_path, value)
            if not os.path.isfile(data_source):
                raise SpecificationViolatedError(
                    'File "{}" not found in folder "{}"'.format(value, self.data_path))
        df = pd.read_csv(data_source, dtype=self._dtypes, converters=self._converters,
                         usecols=self._column_names)
        return self._post_process_dataframe(df)

    def _post_process_dataframe(self, df):
        """Helper method for parse() and coerce()."""
        if self._index is not None:
            df.set_index(self._index, inplace=True, drop=False)
        if self._units_columns:
            df = df.astype({col: float for col in self._units_columns})
            units.autoconvert_offset_to_baseunit = True  # To handle degC units
            for value_col, units_col in self._units_columns.items():
                df[value_col] *= df[units_col]
            units.autoconvert_offset_to_baseunit = False
        return df

    def validate(self, value):
        """Checks that the supplied value is a DataFrame, and its columns match the spec."""
        if not isinstance(value, pd.DataFrame):
            raise SpecificationViolatedError(
                'A Table specification needs to be assigned a DataFrame, not {}'.format(value))
        if set(value.columns) != self._column_names:
            raise SpecificationViolatedError(
                'DataFrame provided has the wrong columns; expected {} not {}'.format(
                    self._column_names, set(value.columns)))
        for col_name, col_spec in self._columns.items():
            if isinstance(col_spec, type):
                if col_spec == str:
                    col_spec = object
                if not np.issubdtype(value[col_name].dtype, col_spec):
                    raise SpecificationViolatedError(
                        'Column {} has the wrong type; expected {} not {}'.format(
                            col_name, col_spec, value[col_name].dtype))
            else:
                assert value[col_name].dtype == object
                for datum in value[col_name]:
                    assert hasattr(datum, 'magnitude')
                    assert isinstance(datum.magnitude, numbers.Number)
        return value

    def coerce(self, value_list):
        """Coerce a list of dictionaries to a table."""
        if isinstance(value_list, dict):
            assert len(value_list) == 1
            value_list = list(value_list.values())[0]
            assert isinstance(value_list, list)
        from copy import deepcopy
        value_list = deepcopy(value_list)
        for row in value_list:
            for name, value in row.items():
                converter = self._converters.get(name)
                if converter:
                    row[name] = converter(value)
        df = pd.DataFrame.from_records(value_list)
        df = self._post_process_dataframe(df)
        # Drop any extra columns
        for col_name in df.columns:
            if col_name not in self._column_names:
                del df[col_name]
        return self.validate(df)


class Nested(Specification):
    """Specify another nested set of parameters."""

    def __init__(self, nested_spec, desc, **kwargs):
        super(Nested, self).__init__(desc, **kwargs)
        self._nested_spec = nested_spec

    def clone(self):
        """We need to clone nested specs too."""
        clone = copy.copy(self)
        for key, spec in clone._nested_spec.items():
            clone._nested_spec[key] = spec.clone()
        return clone

    @property
    def nested(self):
        return self._nested_spec

    def parse(self, value_dict):
        """Parse a dictionary of values."""
        result = {}
        for key, value in value_dict.items():
            try:
                spec = self._nested_spec[key]
            except KeyError:
                raise SpecificationViolatedError(
                    'Name "{}" is not specified'.format(key))
            result[key] = spec.parse(value)
        return result

    def validate(self, value_dict):
        """Check that each value in the given dictionary matches the corresponding spec."""
        for key, value in value_dict.items():
            try:
                spec = self._nested_spec[key]
            except KeyError:
                raise SpecificationViolatedError(
                    'Name "{}" is not specified'.format(key))
            value_dict[key] = spec.validate(value)
        return value_dict

    def coerce(self, value_dict):
        """Coerce each value in the given dict to its own specification."""
        result = {}
        for key, value in value_dict.items():
            try:
                spec = self._nested_spec[key]
            except KeyError:
                raise SpecificationViolatedError(
                    'Name "{}" is not specified'.format(key))
            result[key] = spec.coerce(value)
        return result


class Computed(Specification):
    """Specify a parameter (etc) that is computed on-the-fly from other parameters."""

    def __init__(self, func, desc, **kwargs):
        super(Computed, self).__init__(desc, **kwargs)
        self._func = func

    def clone(self):
        return copy.copy(self)

    def parse(self, value):
        """Parsing values is not permitted."""
        raise SpecificationViolatedError(
            'The value of a Computed specification cannot be set explicitly')

    def validate(self, value):
        """Values can not be set manually."""
        raise SpecificationViolatedError(
            'The value of a Computed specification cannot be set manually')

    def get(self):
        """Get the computed value."""
        return self._func(self.component)


def add_yaml_support():
    """Add support for serialising specified values to YAML.

    Each of the representers added here serialises values in such a way that the
    corresponding spec's parse() method can reconstruct the original value.
    However they do not indicate which spec class to used - this information is
    assumed to be implicit in the parameter name, etc.

    TODO: Nested specs (may be useful for sensitivity).
    """
    import numpy as np
    import yaml

    def represent_quantity(dumper, data):
        """Serialise a quantity with units as a string that Q can parse."""
        return dumper.represent_str('{}'.format(data))

    def represent_enum(dumper, data):
        """Serialise an enum member as a string that Enumerated can parse."""
        return dumper.represent_data(data.name)

    def represent_tuple(dumper, data):
        """Serialise a tuple as a labelled sequence."""
        return dumper.represent_sequence(u'!tuple', data)

    def represent_numpy(dumper, data):
        """Serialise numpy floating point values as standard floats."""
        return dumper.represent_data(float(data))

    dumpers = [yaml.Dumper, yaml.SafeDumper]
    for dumper in dumpers:
        dumper.add_multi_representer(pint.quantity._Quantity, represent_quantity)
        dumper.add_multi_representer(enum.Enum, represent_enum)
        dumper.add_representer(tuple, represent_tuple)
        dumper.add_representer(np.float64, represent_numpy)

    def construct_tuple(loader, node):
        values = loader.construct_sequence(node)
        return tuple(values)

    for loader in [yaml.Loader, yaml.SafeLoader]:
        loader.add_constructor(u'!tuple', construct_tuple)


add_yaml_support()
