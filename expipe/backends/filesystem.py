from ..backend import *
from ..core import *
import pathlib
import os

try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml


def yaml_dump(f, data):
    assert f.suffix == '.yaml'
    with f.open("w", encoding="utf-8") as fh:
        yaml.dump(
            data, fh,
            default_flow_style=False,
            allow_unicode=True,
            Dumper=yaml.RoundTripDumper
        )


def yaml_load(path):
    with path.open('r', encoding='utf-8') as f:
        result = yaml.load(f, Loader=yaml.Loader)


class FileSystemBackend(AbstractBackend):
    def __init__(self, path):
        super(FileSystemBackend, self).__init__(
            path=path
        )
        self.path = pathlib.Path(path)

    def exists(self):
        return self.path.exists()

    def get_project(self):
        return Project(self.path.stem, FileSystemProject(self.path))

    def create_project(self, contents):
        path = self.path
        path.mkdir()
        for p in ['actions', 'entities', 'modules', 'templates']:
            (path / p).mkdir()
        attributes = path / 'attributes.yaml'
        yaml_dump(attributes, contents)
        config_contents = {"type": "project", "database_version": 1}
        config = path / 'expipe.yaml'
        yaml_dump(config, config_contents)
        return Project(self.path.stem, FileSystemProject(path))


class FileSystemObject(AbstractObject):
    def __init__(self, path, object_type, has_attributes=False):
        super(FileSystemObject, self).__init__(
            path=path,
            object_type=object_type
        )
        self.path = path

    def exists(self, name):
        result = yaml_load(self.path)
        return name in result

    def get(self, name=None):
        result = yaml_load(self.path)
        if name is None:
            return result
        else:
            return result[name]

    def set(self, name, value):
        yaml_dump(self.path, value)

    def push(self, value=None):
        raise NotImplementedError("Push not implemented on file system")

    def delete(self, name):
        if value is not None:
            result = self.get(name)
            del result[name]
        yaml_dump(self.path, result)

    def update(self, name, value=None):
        if value is not None:
            result = self.get(name)
            result.update(value)
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
                "does not exist")
        return self._object_type(name, self._backend_type(self.path / name))

    def __iter__(self):
        keys = self.path.iterdir()
        for key in keys:
            yield key.stem

    def __len__(self):
        return len(self.path.iterdir())

    def __contains__(self, name):
        return self.named_path(name).exists()

    def __setitem__(self, name, value):
        if self.has_attributes:
            (self.path / name).mkdir(exist_ok=True)
        yaml_dump(self.named_path(name), value)


class FileSystemProject:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self._attribute_manager = FileSystemObject(self.path, Project)
        self._action_manager = FileSystemObjectManager(
            self.path / "actions", Action, FileSystemAction, has_attributes=True)
        self._entity_manager = FileSystemObjectManager(
            self.path / "entities", Entity, FileSystemEntity, has_attributes=True)
        self._template_manager = FileSystemObjectManager(
            self.path / "templates", Template, FileSystemTemplate, has_attributes=False)
        self._module_manager = FileSystemObjectManager(
            self.path / "modules", Module, FileSystemModule, has_attributes=False)

    @property
    def modules(self):
        return self._module_manager

    @property
    def actions(self):
        print('actions', self.path)
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
        self._attribute_manager = FileSystemObject(path / "attributes.yaml", Action)
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, has_attributes=False)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemModule, has_attributes=False)

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager


class FileSystemEntity:
    def __init__(self, path):
        self.path = path
        self._attribute_manager = FileSystemObject(path / "attributes.yaml", Entity)
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, has_attributes=False)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemModule, has_attributes=False)

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager


class FileSystemModule:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path.with_suffix(".yaml"), Module)

    @property
    def contents(self):
        return self._content_manager


class FileSystemMessage:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path.with_suffix(".yaml"), Message)

    @property
    def contents(self):
        return self._content_manager


class FileSystemTemplate:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path.with_suffix(".yaml"), Template)

    @property
    def contents(self):
        return self._content_manager
