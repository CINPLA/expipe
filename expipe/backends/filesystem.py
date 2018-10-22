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
    def __init__(self, path, object_type):
        super(FileSystemObject, self).__init__(
            path=path,
            object_type=object_type
        )
        if object_type.__name__ in ['Module', 'Template', 'Message']:
            self._suffix = '.yaml'
        elif object_type.__name__ in ['Action', 'Entity', 'Template', 'Project']:
            self._suffix = ''
        self.path = path

    def exists(self, name=None):
        if name is None:
            path = self.path
        else:
            path = self.path / name
        path = path.with_suffix(self._suffix)
        return path.exists()

    def get(self, name=None, shallow=False): # TODO shallow
        if name is None:
            path = self.path
        else:
            path = self.path / name
        try:
            result = yaml_load(path.with_suffix(self._suffix))
        except (IsADirectoryError, FileNotFoundError): # TODO will this work in all cases???
            result = [str(p.stem) for p in path.iterdir()]

        print('get', result)
        return result

    def set(self, name, value=None):
        path = (self.path / name).with_suffix(self._suffix)
        if self._suffix == '':
            path.mkdir(exist_ok=True)
            path = path / 'attributes.yaml'
        print('set', path, value)
        value = value or {}
        yaml_dump(path, value)

    def push(self, value=None):
        pass

    def delete(self, name):
        path = (self.path / name).with_suffix(self._suffix)
        if path.is_dir():
            path.rmdir()
        else:
            assert path.suffix == '.yaml'
            path.unlink()

    def update(self, name, value=None):
        path = (self.path / name).with_suffix(self._suffix)
        if value is not None:
            result = self.get(name)
            result.update(value)
        yaml_dump(path, result)


class FileSystemObjectManager(AbstractObjectManager):
    def __init__(self, path, object_type, backend_type, backend):
        self.path = pathlib.Path(path)
        print('object manager',self.path)
        self._db = FileSystemObject(self.path, object_type)
        self._object_type = object_type
        self._backend_type = backend_type
        self.path.mkdir(exist_ok=True)

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError(
                "{} '{}' ".format(self._object_type.__name__, name) +
                "does not exist")
        print('getit', self._object_type.__name__, name, self.path, self._backend_type.__name__)
        return self._object_type(name, self._backend_type(self.path / name))

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        print('contain', self.path, name, name in (self._db.get(shallow=True) or []))
        return name in (self._db.get(shallow=True) or [])

    def __setitem__(self, name, value):
        self._db.set(name, value)

    def to_dict(self):
        return self._db.get()

class FileSystemProject:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self._attribute_manager = FileSystemObject(self.path, Project)
        self._action_manager = FileSystemObjectManager(
            self.path / "actions", Action, FileSystemAction, self)
        self._entity_manager = FileSystemObjectManager(
            self.path / "entities", Entity, FileSystemEntity, self)
        self._template_manager = FileSystemObjectManager(
            self.path / "templates", Template, FileSystemTemplate, self)
        self._module_manager = FileSystemObjectManager(
            self.path / "modules", Module, FileSystemModule, self)

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
        self._attribute_manager = FileSystemObject(path, Action)
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, self)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemModule, self)

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
        self._attribute_manager = FileSystemObject(path, Entity)
        self._message_manager = FileSystemObjectManager(
            path / "messages", Message, FileSystemMessage, self)
        self._module_manager = FileSystemObjectManager(
            path / "modules", Module, FileSystemModule, self)

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
        self._content_manager = FileSystemObject(path, Module)

    @property
    def contents(self):
        return self._content_manager


class FileSystemMessage:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path, Message)

    @property
    def contents(self):
        return self._content_manager


class FileSystemTemplate:
    def __init__(self, path):
        self.path = path
        self._content_manager = FileSystemObject(path, Template)

    @property
    def contents(self):
        return self._content_manager
