"""Core classes for the PyBioPharma package."""

import collections
import os
import random

import yaml


__all__ = ['BiopharmaError', 'SpecificationViolatedError', 'SpecifiedDict',
           'ModelComponent', 'AnalysisComponent']


class BiopharmaError(RuntimeError):
    """Generic error thrown during a component's execution."""
    pass


class SpecificationViolatedError(AssertionError):
    """Error thrown if an input/output/parameter does not conform to its specification."""
    pass


class SpecifiedDict(collections.UserDict):
    """A dict subclass that ensures values conform to a specification."""

    def __init__(self, spec, dict_name, path='', component=None):
        super(SpecifiedDict, self).__init__()
        self.spec = spec
        self._dict_name = dict_name
        self.path = path
        self.component = component
        self._setup()

    @property
    def data_path(self):
        """The folder in which to look for CSV files referenced by Table specs."""
        return self.component.facility.data_path

    def __getitem__(self, key):
        """Get an entry from the dictionary, allowed the spec to customise reading if required.

        For most kinds of specification this will just delegate to our base class, but if the
        spec defines a get() method this will be used to obtain a value instead.
        """
        spec = self.spec[key]
        if spec.get is not None:
            return spec.get()
        else:
            return super(SpecifiedDict, self).__getitem__(key)

    def __setitem__(self, key, value):
        """Set an entry in the dictionary, if it is allowed by the spec.

        Will raise SpecificationViolatedError if not.
        """
        try:
            spec = self.spec[key]
        except KeyError:
            raise SpecificationViolatedError('{} is not a valid {}'.format(key, self._dict_name))
        try:
            value = spec.validate(value)
        except SpecificationViolatedError as e:
            raise SpecificationViolatedError('Invalid value provided for {} {}: {}'.format(
                self._dict_name, key, str(e)))
        if spec.nested:
            # TODO: This means we validate the nested values twice, which is inefficient
            for nested_name, nested_value in value.items():
                self[key][nested_name] = nested_value
        else:
            super(SpecifiedDict, self).__setitem__(key, value)

    def merge_spec(self, new_spec):
        """Merge another specification into this dictionary.

        :param new_spec: the new specification to merge.
        Any item in new_spec that has already been specified is ignored.
        """
        for key, value in new_spec.items():
            if key not in self.spec:
                self.spec[key] = value.clone()
        self._setup()

    def _setup(self):
        """Set up any special features required by our spec.

        These can be:
        - nested specification dictionaries for Nested spec
        - dummy entries for specs with a get() to ensure the length is correct

        As a side-effect this method ensures that all specs are Specification instances.
        """
        from biopharma.specs import Specification
        for key, spec in self.spec.items():
            if not isinstance(spec, Specification):
                raise ValueError("The class '{}' is not a valid specification type".format(
                    type(spec).__name__))
            spec.component = self.component
            if spec.nested is not None:
                nested_dict = SpecifiedDict(spec.nested, self._dict_name,
                                            path=self.path + '.' + key,
                                            component=self.component)
                super(SpecifiedDict, self).__setitem__(key, nested_dict)
            if spec.get is not None:
                super(SpecifiedDict, self).__setitem__(key, None)


class ModelComponent:
    """Base class for all model components.

    This class takes care of ensuring that assignments to self.inputs, self.outputs and
    self.parameters conform to the specifications in self.INPUTS, self.OUTPUTS and
    self.PARAMETERS.

    Note that we don't restrict who can assign to self.outputs. Rather in 'Pythonic' style
    we assume users of this library are responsible and won't modify outputs after the fact.

    This class also provides core machinery for reading inputs and parameters from YAML files.
    The default parameters file name can be set in __init__, as can a human-oriented name
    for the component. For file loading to work, self.facility must be set to a Facility
    instance with its data_path configured. Most subclasses set this up when they are created
    or assigned to parent components.
    """

    def __init__(self, name=None, param_filename=None):
        """Construct a model component, setting up the inputs etc. dictionaries.

        :param name: user-friendly name of this component, exposed as self.name.
            By default the subclass name is used.
        :param param_filename: name of the file containing this components's parameters.
            The .yaml extension may be omitted. The file should be located in the facility's
            data folder. If no filename is given, the value of the name attribute will be used
            as a default, or the name of the specific subclass if name is None.
        """
        self._create_specified_dict('inputs', 'INPUTS', 'input')
        self._create_specified_dict('outputs', 'OUTPUTS', 'output')
        self._create_specified_dict('parameters', 'PARAMETERS', 'parameter')
        if name is None:
            name = self.__class__.__name__
        self.name = name
        if param_filename is None:
            param_filename = name
        self.param_filename = param_filename
        self.overrides = {}

    def _create_specified_dict(self, attr_name, spec_name, human_name):
        """Set up a new specified dictionary on this object.

        :param attr_name: the name of the attribute to create containing the dictionary
        :param spec_name: the name of the class attribute to read containing the spec
        :param human_name: description of what kind of thing is stored in this dictionary
        """
        d = SpecifiedDict({}, human_name, component=self)
        for klass in type(self).__mro__:
            d.merge_spec(getattr(klass, spec_name, {}))
        setattr(self, attr_name, d)
        setattr(self, spec_name, d.spec)

    def load_parameters(self):
        """Load parameters for this model component from the self.param_filename YAML file."""
        self._load_yaml(self.param_filename, 'parameters', self.parameters, self.PARAMETERS)
        self.apply_overrides()

    def apply_overrides(self):
        """Apply any overrides specified for this component.

        This method is used by the web interface to handle form inputs.
        """
        for item, value in self.overrides.items():
            # item is a tuple containing collection name and parameter name
            coll, param = item
            collection = getattr(self, coll)
            spec = collection.spec.get(param)
            if spec:
                collection[param] = spec.coerce(value)

    def load_inputs(self, filename):
        """Load inputs for this model component from a YAML file.

        :param filename: name of the file containing inputs (optionally minus extension).
            The file should be located in the facility's data folder.
        """
        self._load_yaml(filename, 'inputs', self.inputs, self.INPUTS)

    def _load_yaml(self, filename, section, target_dict, specs):
        """Internal helper method used by the load_* methods."""
        basename, extension = os.path.splitext(filename)
        if extension == '':
            extension = '.yaml'
        data_path = os.path.join(self.facility.data_path, basename + extension)
        with open(data_path) as data_file:
            data = yaml.safe_load(data_file)
        # Parse all entries according to our spec
        for key, value in data[section].items():
            assert key in specs, 'The name {} is not in {}; check spelling?'.format(key, section)
            target_dict[key] = specs[key].parse(value)

    def extract_outputs(self, collection='outputs'):
        """Extract this component's outputs as a plain dictionary.

        :param collection: the name of the collection to extract, e.g. to select parameters instead
        """
        def process_dict(d):
            result = {}
            for name, value in d.items():
                if isinstance(value, SpecifiedDict):
                    result[name] = process_dict(value)
                else:
                    result[name] = value
            return result
        result = {'name': self.name}
        result.update(process_dict(getattr(self, collection)))
        return result

    def save_outputs(self, path, collection='outputs'):
        """Save this component's outputs to a YAML file.

        :param path: path to file to write. If relative, will be resolved relative to the
            facility's data folder. A .yaml extension will be added if no extension is given.
        :param collection: the name of the collection to extract, e.g. to save parameters instead
        """
        basename, extension = os.path.splitext(path)
        if extension == '':
            extension = '.yaml'
        path = os.path.join(self.facility.data_path, basename + extension)
        data = self.extract_outputs(collection=collection)
        with open(path, 'w') as output_file:
            yaml.dump(data, output_file, default_flow_style=False)


class AnalysisComponent(ModelComponent):
    """A base class for components which perform higher-level operations on a model."""

    def get_seed(self):
        """Obtain the current seed of the random number generator used."""
        return random.getstate()

    def set_seed(self, state):
        """Set the state of the random number generator.

        :param state: a state returned by the get_seed() method
        """
        random.setstate(state)
