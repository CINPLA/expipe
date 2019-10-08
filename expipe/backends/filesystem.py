from ..backend import *
from ..core import Action, Entity, Project, Module, Message, MapManager, Template
import quantities as pq
import numpy as np
import pathlib
import shutil
import os

try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml

# TODO move into plugin
def convert_back_quantities(value):
    """Convert quantities back from dictionary."""
    result = value
    if isinstance(value, dict):
        if "unit" in value and "value" in value and "uncertainty" in value:
            try:
                result = pq.UncertainQuantity(value["value"],
                                              value["unit"],
                                              value["uncertainty"])
            except Exception:
                pass
        elif "unit" in value and "value" in value:
            try:
                result = pq.Quantity(value["value"], value["unit"])
            except Exception:
                pass
        else:
            try:
                for key, value in result.items():
                    result[key] = convert_back_quantities(value)
            except AttributeError:
                pass

    return result


def convert_quantities(value):
    """Convert quantities to dictionary."""

    result = value
    if isinstance(value, pq.Quantity):
        result = {
            "value": value.magnitude.tolist(),
            "unit": value.dimensionality.string
        }
        if isinstance(value, pq.UncertainQuantity):
            assert value.dimensionality == value.uncertainty.dimensionality
            result["uncertainty"] = value.uncertainty.magnitude.tolist()
    elif isinstance(value, np.ndarray):
        result = value.tolist()
    elif isinstance(value, np.integer):
        result = int(value)
    elif isinstance(value, np.float):
        result = float(value)
    else:
        # try if dictionary like objects can be converted if not return the
        # original object
        # Note, this might fail if .items() returns a strange combination of
        # objects
        try:
            new_result = {}
            for key, val in value.items():
                new_key = convert_quantities(key)
                new_result[new_key] = convert_quantities(val)
            result = new_result
        except AttributeError:
            pass

    return result


def yaml_dump(f, data):
    assert f.suffix == '.yaml'
    with f.open("w", encoding="utf-8") as fh:
        yaml.dump(
            convert_quantities(data), fh,
            default_flow_style=False,
            allow_unicode=True,
            Dumper=yaml.RoundTripDumper
        )


def yaml_load(path):
    with path.open('r', encoding='utf-8') as f:
        result = yaml.load(f, Loader=yaml.Loader)
    return convert_back_quantities(result)


class FileSystemObject(AbstractObject):
    def __init__(self, path):
        self.path = path

    def exists(self, name):
        result = yaml_load(self.path)
        return name in result

    def get(self, name=None):
        result = yaml_load(self.path) or {}
        if name is None:
            return result
        else:
            return result.get(name)

    def set(self, name, value):
        result = self.get()
        result[name] = value
        yaml_dump(self.path, result)

    def push(self, value=None):
        raise NotImplementedError("Push not implemented on file system")

    def delete(self, name):
        if name is not None:
            result = self.get(name)
            del result[name]
        yaml_dump(self.path, result)

    def update(self, name, value=None):
        if value is not None:
            result = self.get(name)
            result[name].update(value)
        yaml_dump(self.path, result)


class FileSystemObjectManager(AbstractObjectManager):
    def __init__(self, path, object_type, backend_type, has_attributes=False):
        self.path = pathlib.Path(path)
        self._object_type = object_type
        self._backend_type = backend_type
        self.path.mkdir(exist_ok=True)
        self.has_attributes = has_attributes

    def named_path(self, name):
        if self.has_attributes:
            return (self.path / name / "attributes.yaml")
        else:
            return (self.path / name).with_suffix(".yaml")

    def __getitem__(self, name):
        if not self.named_path(name).exists():
            raise KeyError(
                "{} '{}' ".format(self._object_type.__name__, name) +
                "does not exist in {}".format(self.named_path(name)))
        return self._object_type(name, self._backend_type(self.path / name))

    def __iter__(self):
        keys = self.path.iterdir()
        for key in keys:
            yield key.stem

    def __len__(self):
        return len(list(self.path.iterdir()))

    def __contains__(self, name):
        return self.named_path(name).exists()

    def __setitem__(self, name, value):
        if self.has_attributes:
            (self.path / name).mkdir(exist_ok=True)
        yaml_dump(self.named_path(name), value)

    def delete(self, name):
        if self.has_attributes:
            path = self.path / name
        else:
            path = (self.path / name).with_suffix(".yaml")
        if path.is_dir():
            assert path != self.path.root
            shutil.rmtree(str(path))
        else:
            path.unlink()


class FileSystemYamlManager(AbstractObjectManager):
    def __init__(self, path, ref_path=None):
        self.path = path.with_suffix('.yaml')
        self.ref_path = ref_path or []

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, value_if_missing=None):
        result = self._get_yaml_contents()
        try:
            for p in self.ref_path:
                result = result[p]
            result = result.get(name, value_if_missing)
        except KeyError:
            result = value_if_missing

        if isinstance(result, dict):
            result = MapManager(FileSystemYamlManager(self.path, self.ref_path + [name]))

        return result

    def __eq__(self, other):
        result = self._get_yaml_contents()
        for p in self.ref_path:
            result = result[p]
        return result == other

    def keys(self):
        result = self._get_yaml_contents()
        for p in self.ref_path:
            result = result[p]
        return result.keys()

    def values(self):
        result = self._get_yaml_contents()
        for p in self.ref_path:
            result = result[p]
        return result.keys()

    def __iter__(self):
        for key in self.contents:
            yield key

    def __len__(self):
        return len(self.contents)

    def __contains__(self, name):
        return name in self.contents

    def __setitem__(self, name, value):
        result = self._get_yaml_contents()
        sub_result = result

        for p in self.ref_path:
            try:
                sub_result = sub_result[p]
            except KeyError:
                sub_result[p] = {}
                sub_result = sub_result[p]

        sub_result[name] = value
        yaml_dump(self.path, result)

    def _get_yaml_contents(self):
        result = yaml_load(self.path) or {}
        return result

    @property
    def contents(self):
        result = self._get_yaml_contents()
        for p in self.ref_path:
            result = result[p]
        return result


class FileSystemProject:
    def __init__(self, path, config):
        self.path = pathlib.Path(path)
        self.config = config
        self._attribute_manager = FileSystemObject(self.path)
        self._action_manager = FileSystemObjectManager(
            self.path / "actions", Action, FileSystemAction, has_attributes=True)
        self._entity_manager = FileSystemObjectManager(
            self.path / "entities", Entity, FileSystemEntity, has_attributes=True)
        self._template_manager = FileSystemObjectManager(
            self.path / "templates", Template, FileSystemYamlManager)
        self._module_manager = FileSystemObjectManager(
            self.path / "modules", Module, FileSystemYamlManager)

    @property
    def modules(self):
        return self._module_manager

    @property
    def actions(self):
        return self._action_manager

    @property
    def entities(self):
        return self._entity_manager

    @property
    def templates(self):
        return self._template_manager

    @property
    def attributes(self):
        return self._attribute_manager


class FileSystemAction:
    def __init__(self, path):
        self.path = path
        project = self.path.parent
        if project.stem == 'actions': #TODO consider making project path global
            project = project.parent
        self._project_path = project
        self._attribute_manager = FileSystemObject(path / "attributes.yaml")
        self._data_manager = FileSystemYamlManager(path / "attributes.yaml")
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, has_attributes=False)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemYamlManager)
        self._template_manager = FileSystemObjectManager(
            project / "templates", Template, FileSystemYamlManager)

    @property
    def templates(self):
        return self._template_manager

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager

    @property
    def data(self):
        return self._data_manager.get('data', {})

    def data_path(self, key=None):
        (self.path / "data").mkdir(exist_ok=True)
        if key is not None:
            return self.path / "data" / self.data[key]
        else:
            return self.path / "data"


class FileSystemEntity:
    def __init__(self, path):
        self.path = path
        project = self.path.parent
        if project.stem == 'entities': #TODO
            project = project.parent
        self._attribute_manager = FileSystemObject(path / "attributes.yaml")
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, has_attributes=False)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemYamlManager)
        self._template_manager = FileSystemObjectManager(
            project / "templates", Template, FileSystemYamlManager)

    @property
    def templates(self):
        return self._template_manager

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager


class FileSystemMessage:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path.with_suffix(".yaml"))

    @property
    def contents(self):
        return self._content_manager


class FileSystemTemplate:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path.with_suffix(".yaml"))

    @property
    def contents(self):
        return self._content_manager
