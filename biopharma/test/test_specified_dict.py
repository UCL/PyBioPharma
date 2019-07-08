from biopharma import units
from biopharma.core import SpecifiedDict, ModelComponent, SpecificationViolatedError
from biopharma.specs import Q, Value, Nested, Computed

import numbers
from pytest import raises


def test_class_instances():
    class MyRandomClass(object):
        def __init__(self, val):
            self.val = val
    spec = {
        'mine': Value(MyRandomClass, ''),
        'int': Value(int, ''),
        'float': Value(float, ''),
        'number': Value(numbers.Number, '')
    }
    d = SpecifiedDict(spec, 'test')
    d['mine'] = MyRandomClass(2)
    assert d['mine'].val == 2
    with raises(SpecificationViolatedError) as excinfo:
        d['mine'] = 2
    excinfo.match(r'')
    d['int'] = 1
    assert d['int'] == 1
    with raises(SpecificationViolatedError) as excinfo:
        d['int'] = 1.5
    excinfo.match(r'Invalid value provided for test int: Value "1\.5" is not an instance of .*int')
    d['float'] = 1.5
    assert d['float'] == 1.5
    with raises(SpecificationViolatedError):
        d['float'] = 1
    d['float'] = 1.
    assert d['float'] == 1
    d['number'] = 1.5
    assert d['number'] == 1.5
    d['number'] = 1
    assert d['number'] == 1


def test_units():
    spec = {
        'dless': Q('dimensionless', ''),
        'count': Q('count', ''),
        'metre': Q('metre', ''),
        'm_per_s': Q('m / s', ''),
        'money': Q('GBP', '')
    }
    d = SpecifiedDict(spec, 'test')
    d['dless'] = units.Quantity(1)
    assert d['dless'].magnitude == 1
    assert d['dless'].units == units.dimensionless
    d['count'] = 2
    assert d['count'] == 2
    assert d['count'] == 2 * units.count
    assert d['count'].units == units.count
    d['count'] = units('4')
    assert d['count'] == 4
    d['metre'] = 3 * units.m
    assert d['metre'] == 3 * units.m
    d['metre'] = 3 * units.cm
    assert d['metre'].units == units.m
    assert d['metre'] == 0.03 * units.m
    d['metre'] = units('1 m')
    assert d['metre'] == 1 * units.m
    d['metre'] = units('2 * m')
    assert d['metre'] == 2 * units.m
    d['m_per_s'] = 4 * (units.m ** 2) / (units.m * units.s)
    assert d['m_per_s'] == 4 * units.m / units.s
    d['money'] = 5 * units.GBP
    assert d['money'] == 5 * units.GBP
    d['money'] = 5 * units.EUR
    assert d['money'] == 0.8 * 5 * units.GBP

    with raises(SpecificationViolatedError) as excinfo:
        d['metre'] = 2
    excinfo.match(r'Invalid value provided for test metre: '
                  r'Number "2" provided but quantity with units meter required')
    with raises(SpecificationViolatedError) as excinfo:
        d['metre'] = 2 * units.s
    excinfo.match(r'Invalid value provided for test metre: '
                  r'Value "2 second" does not have units meter')


def test_bad_spec():
    spec = {
        'none': None,
    }
    with raises(ValueError) as excinfo:
        d = SpecifiedDict(spec, 'test')  # noqa
    excinfo.match(r"The class 'NoneType' is not a valid specification type")


def test_use_from_modelcomponent():
    class MyComponent(ModelComponent):
        INPUTS = {'i1': Q('m', '')}
        OUTPUTS = {'o1': Q('s', '')}
        PARAMETERS = {
            'p1': Value(int, ''),
            'c': Computed(lambda self: self.inputs['i1'] * self.parameters['p1'],
                          '')}
    inst = MyComponent()
    assert len(inst.inputs) == 0
    assert len(inst.outputs) == 0
    assert len(inst.parameters) == 1

    with raises(KeyError):
        # A value used in the equation hasn't been set yet
        assert inst.parameters['c'] is None

    inst.inputs['i1'] = -1 * units.metre
    assert inst.inputs['i1'].magnitude == -1
    inst.outputs['o1'] = 1000 * units.ms
    assert inst.outputs['o1'] == 1 * units.s
    assert inst.outputs['o1'].units == units.s
    inst.parameters['p1'] = 5
    assert inst.parameters['p1'] == 5
    inst.parameters['p1'] = 50
    assert inst.parameters['p1'] == 50
    assert inst.parameters['c'] == -50 * units.m
    assert len(inst.inputs) == 1
    assert len(inst.outputs) == 1
    assert len(inst.parameters) == 2

    with raises(SpecificationViolatedError):
        inst.parameters['p2'] = 2

    with raises(SpecificationViolatedError):
        inst.parameters['c'] = 2 * units.m


def test_nested_specs():
    class Component(ModelComponent):
        INPUTS = {
            'normal': Value(bool, ''),
            'nest1': Nested({
                'sub1': Value(int, ''),
                'nest2': Nested({
                    'sub2': Value(float, '')
                }, '')
            }, '')
        }
        OUTPUTS = {}
        PARAMETERS = {}

    inst = Component()
    assert len(inst.inputs) == 1
    assert 'nest1' in inst.inputs
    assert isinstance(inst.inputs['nest1'], SpecifiedDict)
    assert len(inst.inputs['nest1']) == 1
    assert 'nest2' in inst.inputs['nest1']
    assert isinstance(inst.inputs['nest1']['nest2'], SpecifiedDict)
    assert inst.inputs.path == ''
    assert inst.inputs['nest1'].path == '.nest1'
    assert inst.inputs['nest1']['nest2'].path == '.nest1.nest2'

    inst.inputs['nest1']['nest2']['sub2'] = 2.0
    assert inst.inputs['nest1']['nest2']['sub2'] == 2.0
    inst.inputs['nest1']['sub1'] = -1
    assert inst.inputs['nest1']['sub1'] == -1
    inst.inputs['normal'] = True
    assert inst.inputs['normal']


def test_inheriting_specs():
    class BaseComponent(ModelComponent):
        INPUTS = {'b1': Q('m', 'Base b1'),
                  'b2': Q('s', 'Base b2'),
                  'b3': Q('L', 'Base b3')}
        OUTPUTS = {}
        PARAMETERS = {}

    class MiddleComponent(BaseComponent):
        INPUTS = {'b1': Value(int, 'Middle b1'),
                  'b3': Q('m', 'Middle b3'),
                  'm1': Q('count', 'Middle m1'),
                  'm2': Q('GBP', 'Middle m2')}

    class SubComponent(MiddleComponent):
        INPUTS = {'m2': Value(float, 'Sub m2'),
                  'b3': Value(float, 'Sub b3'),
                  's1': Value(float, 'Sub s1')}

    inst = SubComponent()
    assert len(inst.inputs) == 0
    assert len(inst.outputs) == 0
    assert len(inst.parameters) == 0
    expected_full_spec = {
        'b1': Value(int, 'Middle b1'),
        'b2': Q('s', 'Base b2'),
        'b3': Value(float, 'Sub b3'),
        'm1': Q('count', 'Middle m1'),
        'm2': Value(float, 'Sub m2'),
        's1': Value(float, 'Sub s1')
    }
    assert inst.INPUTS == expected_full_spec

    inst.inputs['b1'] = 1
    assert inst.inputs['b1'] == 1
    inst.inputs['b2'] = 1 * units.s
    assert inst.inputs['b2'] == 1 * units.s
    inst.inputs['b3'] = 1.0
    assert inst.inputs['b3'] == 1.0

    inst.inputs['m1'] = 2 * units.count
    assert inst.inputs['m1'] == 2 * units.count
    inst.inputs['m2'] = 2.0
    assert inst.inputs['m2'] == 2.0

    inst.inputs['s1'] = 3.0
    assert inst.inputs['s1'] == 3.0

    with raises(SpecificationViolatedError):
        inst.inputs['b1'] = 1 * units.m
    with raises(SpecificationViolatedError):
        inst.inputs['b3'] = 1 * units.L
    with raises(SpecificationViolatedError):
        inst.inputs['b3'] = 1 * units.m
    with raises(SpecificationViolatedError):
        inst.inputs['m2'] = 2 * units.GBP
