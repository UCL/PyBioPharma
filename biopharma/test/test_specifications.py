
from biopharma import units
from biopharma.core import SpecificationViolatedError
from biopharma.specs import *

from enum import Enum
import os
from math import inf

import pandas as pd

import pytest
from pytest import fixture, raises


def test_quantity_specs():
    spec = Q('m', 'desc')
    assert spec.description == 'desc'
    assert spec.parse('1 metre') == 1 * units.m
    assert spec.parse('1.2 cm') == 1.2 * units.cm

    with raises(SpecificationViolatedError):
        spec.parse('1')

    with raises(SpecificationViolatedError):
        spec.parse('1 metress')

    with raises(SpecificationViolatedError):
        spec.parse('1 second')

    assert spec.nested is None
    assert spec.get is None
    assert not spec.hidden
    assert spec.zero == 0 * units.m
    assert spec.zero.units == units.m
    assert spec.inf == inf * units.m
    assert spec.inf.units == units.m

    new_spec = spec.with_same_units('new desc')
    assert new_spec.units == spec.units
    assert new_spec.description == 'new desc'

    new_spec = spec.with_squared_units('new desc')
    assert new_spec.units == spec.units * spec.units
    assert new_spec.description == 'new desc'

    assert spec.coerce(2) == 2 * units.m
    assert spec.coerce(3 * units.m) == 3 * units.m
    with raises(SpecificationViolatedError):
        spec.coerce(1 * units.s)
    with raises(AttributeError):
        spec.coerce('1')


def test_bool_value_spec():
    spec = Value(bool, 'my desc')
    assert spec.description == 'my desc'
    assert spec.parse(True) is True
    assert spec.parse(False) is False

    with raises(SpecificationViolatedError):
        spec.parse('True')

    assert spec.nested is None
    assert spec.get is None
    assert not spec.hidden

    assert spec.coerce(True) is True
    assert spec.coerce(2) is True


def test_float_value_spec():
    spec = Value(float, 'float desc!')
    assert spec.description == 'float desc!'
    assert spec.parse(1.0) == 1.0
    assert spec.parse(-1.5) == -1.5
    assert spec.parse(2) == 2.0
    assert type(spec.parse(2.0)) is float
    assert type(spec.parse(2)) is float

    with raises(SpecificationViolatedError):
        spec.parse('2.5')

    assert spec.nested is None
    assert spec.get is None
    assert not spec.hidden

    assert spec.coerce(1.5) == 1.5
    assert spec.coerce(True) == 1
    assert spec.coerce('2') == 2
    with raises(ValueError):
        spec.coerce('one')


def test_hidden_spec():
    spec = Q('s', 'desc', hidden=True)
    assert spec.hidden
    assert spec.description == 'desc'
    assert spec.parse('55 s') == 55 * units.s


def test_enum_specs():
    class E(Enum):
        v1 = 1
        v2 = 2

    spec = Enumerated(E, 'enum')
    assert spec.description == 'enum'
    assert spec.parse(1) is E.v1
    assert spec.parse('v2') is E.v2

    with raises(SpecificationViolatedError):
        spec.parse(3)

    with raises(SpecificationViolatedError):
        spec.parse('v3')

    assert spec.nested is None
    assert spec.get is None
    assert not spec.hidden

    assert spec.coerce(E.v1) is E.v1
    assert spec.coerce('v1') is E.v1
    with raises(SpecificationViolatedError):
        spec.coerce(3)


@fixture
def mock_component():
    """Provide just enough of the ModelComponent interface for SpecifiedDict."""
    class C:
        pass
    comp = C()
    comp.facility = comp
    root_folder = os.path.dirname(__file__)
    comp.data_path = os.path.join(root_folder, 'data')
    return comp


def test_table_spec_eq(mock_component):
    eq_spec = Table(
        columns={'EqName': str,
                 'Function': str,
                 'CostIndex': float,
                 'Size': in_units(col='Units'),
                 'Cost': in_units(col='Currency'),
                 'Diameter': in_units('cm')
                 },
        index='EqName',
        desc='$Table eq.',
        column_descs={'Size': 'Eq size', 'Cost': 'Reference cost'})

    assert eq_spec.description == '$Table eq.'
    assert len(eq_spec.column_descriptions) == 6
    assert eq_spec.column_descriptions['Size'] == 'Eq size'
    assert eq_spec.column_descriptions['Cost'] == 'Reference cost'
    assert eq_spec.column_descriptions['EqName'] == 'EqName'
    assert eq_spec.column_descriptions['Diameter'] == 'Diameter'
    assert eq_spec.column_descriptions['Function'] == 'Function'
    assert eq_spec.column_descriptions['CostIndex'] == 'CostIndex'

    eq_spec.component = mock_component
    eq = eq_spec.parse('equipment.csv')

    assert isinstance(eq, pd.DataFrame)
    assert eq.index.name == 'EqName'
    assert eq.index.dtype == object
    for i in range(len(eq)):
        assert hasattr(eq['Size'].iloc[i], 'units')
        assert eq['Size'].iloc[i].units == eq['Units'].iloc[i]
        assert hasattr(eq['Cost'].iloc[i], 'units')
        assert eq['Cost'].iloc[i].units == eq['Currency'].iloc[i]
        assert eq['Diameter'].iloc[i].units == units.cm
    assert eq['CostIndex'].dtype == float

    # Check we only have the columns specified
    assert set(eq.columns) == {
        'EqName', 'Function', 'CostIndex', 'Size', 'Units', 'Cost', 'Currency', 'Diameter'}

    assert eq_spec.nested is None
    assert eq_spec.get is None
    assert not eq_spec.hidden


class MyEnum(Enum):
    """A simple Enum for testing specs."""
    v1 = 1
    v2 = 2


def test_table_with_enumeration(mock_component):
    spec = Table(
        columns={'ID': int,
                 'Mode': MyEnum,
                 'SingleUse': bool,
                 },
        index='ID',
        desc='')

    spec.component = mock_component
    resins = spec.parse('resins.csv')

    assert 'Mode' in resins.columns
    assert resins['Mode'].dtype == object
    for i in range(len(resins)):
        assert isinstance(resins['Mode'].iloc[i], MyEnum)


@fixture
def table_spec():
    """A common sample table spec for tests below."""
    spec = Table(
        columns={'ID': int, 'CmCol': in_units('cm'), 'BoolCol': bool,
                 'QuantCol': in_units(col='UnitsCol'), 'EnumCol': MyEnum},
        index='ID',
        desc='desc')

    assert spec.nested is None
    assert spec.get is None
    assert not spec.hidden

    return spec


def check_table_data(data):
    """Common checks for table tests below using the table_spec fixture."""
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 3
    assert data.index.name == 'ID'

    assert data['CmCol'].loc[1].units == units.cm
    assert data['CmCol'].loc[1] == 1 * units.cm
    assert data['CmCol'].loc[2] == 2 * units.cm
    assert data['CmCol'].loc[3] == 3 * units.cm

    assert data['BoolCol'].dtype == bool
    assert data['BoolCol'].loc[1]
    assert not data['BoolCol'].loc[2]
    assert data['BoolCol'].loc[3]

    assert data['EnumCol'].dtype == object
    assert data['EnumCol'].loc[1] is MyEnum.v1
    assert data['EnumCol'].loc[2] is MyEnum.v2
    assert data['EnumCol'].loc[3] is MyEnum.v1

    assert data['QuantCol'].loc[1].units == units.m
    assert data['QuantCol'].loc[1] == 100.0 * units.m
    assert data['QuantCol'].loc[2] == 200.0 * units.s
    assert data['QuantCol'].loc[3] == 300.0 * units.kg

    # Check we only have the columns specified
    assert set(data.columns) == {'ID', 'CmCol', 'BoolCol', 'QuantCol', 'UnitsCol', 'EnumCol'}


def test_table_from_csv_string(table_spec):
    data = table_spec.parse('&CSV::ID,CmCol,BoolCol,QuantCol,UnitsCol,EnumCol\n'
                            '1,1,True,100.0,m,v1\n'
                            '2,2,False,200.0,s,2\n'
                            '3,3,True,300.0,kg,1\n')
    check_table_data(data)


def test_table_from_dataframe(table_spec):
    df = pd.DataFrame({'CmCol': [1 * units.cm, 2 * units.cm, 3 * units.cm],
                       'BoolCol': [True, False, True],
                       'UnitsCol': ['m', 's', 'kg'],
                       'QuantCol': [100.0 * units.m, 200.0 * units.s, 300.0 * units.kg],
                       'EnumCol': [MyEnum.v1, MyEnum.v2, MyEnum.v1],
                       'ID': [1, 2, 3]})
    df.set_index('ID', inplace=True, drop=False)
    data = table_spec.parse(df)
    check_table_data(data)


@pytest.mark.skip(reason="causes a pandas indexing warning")
def test_table_from_dataframe_string_quantities(table_spec):
    df = pd.DataFrame({'CmCol': ['1 cm', 'nan', '3 cm'],
                       'BoolCol': [True, False, True],
                       'UnitsCol': ['m', 's', 'kg'],
                       'QuantCol': ['100.0 m', '200.0 s', '300.0 kg'],
                       'EnumCol': [MyEnum.v1, MyEnum.v2, MyEnum.v1],
                       'ID': [1, 2, 3]})
    df.set_index('ID', inplace=True, drop=False)
    data = table_spec.parse(df)
    from math import isnan
    assert isnan(data['CmCol'].loc[2].magnitude)
    data['CmCol'].loc[2] = 2 * units.cm
    check_table_data(data)


def test_table_coercion(table_spec):
    value_list = [{'ID': 1, 'CmCol': 1 * units.cm, 'BoolCol': True,
                   'QuantCol': 100.0, 'UnitsCol': 'm', 'EnumCol': '1'},
                  {'ID': 2, 'CmCol': 2 * units.cm, 'BoolCol': False,
                   'QuantCol': '200.0', 'UnitsCol': 's', 'EnumCol': 'v2'},
                  {'ID': 3, 'CmCol': 3 * units.cm, 'BoolCol': True,
                   'QuantCol': '300.0', 'UnitsCol': 'kg', 'EnumCol': MyEnum.v1}]
    data = table_spec.coerce(value_list)
    check_table_data(data)


def test_table_coercion_like_server(table_spec):
    value_list = {'rows': [{'ID': 1, 'CmCol': '1 cm', 'BoolCol': True, 'NotCol': '300',
                            'QuantCol': '100.0', 'UnitsCol': 'm', 'EnumCol': '1'},
                           {'ID': 2, 'CmCol': '2 cm', 'BoolCol': False, 'NotCol': '400',
                            'QuantCol': 200.0, 'UnitsCol': 's', 'EnumCol': 'v2'},
                           {'ID': 3, 'CmCol': '3 cm', 'BoolCol': True, 'NotCol': '400',
                            'QuantCol': 300.0, 'UnitsCol': 'kg', 'EnumCol': MyEnum.v1}]}
    data = table_spec.coerce(value_list)
    check_table_data(data)


def test_nested_specs():
    spec = Nested({
        'sub1': Q('m', 'sub1 desc'),
        'sub2': Value(bool, 'sub2 desc', hidden=True),
        'nest': Nested({
            'sub3': Q('s', 'sub3 desc')
        }, 'inner desc')
    }, 'outer desc')

    # Check descriptions
    assert spec.description == 'outer desc'
    assert spec.nested['sub1'].description == 'sub1 desc'
    assert spec.nested['nest'].description == 'inner desc'
    assert spec.nested['nest'].nested['sub3'].description == 'sub3 desc'

    # Check we can fill the whole dict from "YAML"
    data = {
        'sub1': '1 metre',
        'sub2': False,
        'nest': {
            'sub3': '2 s'
        }
    }
    value = spec.parse(data)

    assert len(value) == 3
    assert value['sub1'] == 1 * units.m
    assert value['sub2'] is False
    assert isinstance(value['nest'], dict)
    assert len(value['nest']) == 1
    assert value['nest']['sub3'] == 2 * units.s

    # Check we can assign individual items
    value['sub1'] = 3 * units.m
    assert value['sub1'] == 3 * units.m
    value['nest']['sub3'] = 4 * units.s
    assert value['nest']['sub3'] == 4 * units.s

    assert spec.get is None

    assert not spec.hidden
    assert not spec.nested['sub1'].hidden
    assert spec.nested['sub2'].hidden
    assert not spec.nested['nest'].hidden
    assert not spec.nested['nest'].nested['sub3'].hidden

    # Check coercion
    value = spec.coerce({
        'sub1': 1,
        'sub2': 0,
        'nest': {
            'sub3': 2
        }
    })
    assert len(value) == 3
    assert value['sub1'] == 1 * units.m
    assert value['sub2'] is False
    assert isinstance(value['nest'], dict)
    assert len(value['nest']) == 1
    assert value['nest']['sub3'] == 2 * units.s


def test_computed_spec_simple(mock_component):
    constant = 2.5
    desc = 'Our description'
    spec = Computed(lambda self: constant, desc)
    spec.component = mock_component

    assert spec.description == desc
    assert spec.get() == constant

    # Setting the value should fail
    with raises(SpecificationViolatedError):
        spec.parse('1')
    with raises(SpecificationViolatedError):
        spec.validate(1)

    assert spec.nested is None
    assert not spec.hidden


def test_computed_spec_obj_access(mock_component):
    spec = Computed(lambda self: self.param * 2, 'Desc')
    spec.component = mock_component

    mock_component.param = 3.0
    assert spec.get() == 6.0

    mock_component.param = -2 * units.m
    assert spec.get() == -4 * units.m

    # Setting the value should still fail
    with raises(SpecificationViolatedError):
        spec.parse('1')
    with raises(SpecificationViolatedError):
        spec.validate(1)


@pytest.mark.parametrize('spec_type, arg', [
    (Q, 'm'),
    (Value, bool),
    (Enumerated, Enum('E', '1,2,3')),
    (Computed, lambda self: 1),
    (Nested, {'sub1': Q('m', 'sub1 desc'),
              'nest': Nested({
                  'sub2': Q('s', 'sub2 desc')
              }, 'inner desc')}),
    (Table, {'Name': str})
])
def test_cloning(mock_component, spec_type, arg):
    if spec_type is Table:
        spec = spec_type(columns=arg, desc='Desc', hidden=True)
    else:
        spec = spec_type(arg, desc='Desc')
    spec.component = mock_component
    clone = spec.clone()
    assert clone.description == spec.description
    assert clone.component is mock_component
    clone.component = None
    assert spec.component is mock_component
    assert clone.hidden == spec.hidden


@pytest.mark.parametrize('spec_type, arg, input, result', [
    (Q, 'm', '2 metres', 2 * units.m),
    (Value, bool, True, True),
    (Value, tuple, (1, '2', 3.4), (1, '2', 3.4)),
    (Enumerated, MyEnum, 'v1', MyEnum.v1),
])
def test_yaml_roundtrip(spec_type, arg, input, result):
    spec = spec_type(arg, desc='Description')
    value = spec.parse(input)
    assert value == result

    # Now serialise to YAML and re-parse
    import yaml
    serialised = yaml.dump(value)
    print(serialised)
    loaded = yaml.safe_load(serialised)
    assert spec.parse(loaded) == result
