from ..backend import *
from ..core import *
import pathlib
import os
import yaml

class FileSystemBackend(AbstractBackend):
    def __init__(self, path):
        # super(FileSystemBackend, self).__init__(
        #     path=path
        # )

        self.path = pathlib.Path(path)
        self.root, self.config = self.discover_config(path)

    @property
    def projects(self):
        return FileSystemObjectManager("projects", Project, FileSystemProject, self)

    def create_project(self, project_id, contents):
        path = self.path / project_id
        path.mkdir(exist_ok=True)
        attributes = path / 'attributes.yaml'
        with attributes.open("w", encoding="utf-8") as f:
            yaml.dump(
                contents, f,
                default_flow_style=False,
                allow_unicode=True
            )
        return FileSystemProject(path)

    def discover_config(self, path):
        current_path = pathlib.Path(path)
        config_filename = current_path / "expipe.yaml"
        if not config_filename.exists():
            if current_path.match(config_filename.root):
                raise Exception(
                    "ERROR: No expipe.yaml found in '" + str(self.path) + "' or parents.")

            return self.discover_config(current_path.parent)


        with config_filename.open('r', encoding="utf-8") as f:
            return current_path, yaml.load(f)


class FileSystemObject(AbstractObject):
    def __init__(self, path):
        # super(FileSystemObject, self).__init__(
        #     path=path
        # )
        self.path = path

    def exists(self, name=None):
        if name is None:
            path = self.path
        else:
            path = self.path / name
        return path.exists()

    def get(self, name=None, shallow=False):
        if name is None:
            path = self.path
            name = self.path.stem
        else:
            path = self.path / name
        if shallow:
            if path.suffix != '.yaml':
                result = path.iterdir()
            else:
                with path.open('r', encoding='utf-8') as f:
                    result = yaml.load(f)
        else:
            raise NotImplementedError
        return result

    def set(self, name, value=None):
        path = self.path / name
        value = value or {}
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(
                value, f,
                default_flow_style=False,
                allow_unicode=True
            )

    def push(self, value=None):
        pass

    def delete(self, name):
        path = self.path / name
        os.remove(path)

    def update(self, name, value=None):
        path = self.path / name
        if value is not None:
            result = self.get(name)
            result.update(value)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(
                result, f,
                default_flow_style=False,
                allow_unicode=True
            )


class FileSystemObjectManager(AbstractObjectManager):
    def __init__(self, path, object_type, backend_type, backend):
        self._db = FileSystemObject(pathlib.Path(path))
        self._object_type = object_type
        self._backend_type = backend_type

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Action '{}' does not exist".format(name))
        return self._object_type(self._backend_type(name))

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        return name in (self._db.get(shallow=True) or [])

    def __setitem__(self, name, value):
        self._db.set(name, value)

    def to_dict(self):
        return self._db.get()

class FileSystemProject:
    def __init__(self, name):
        self._name = name
        self._attribute_manager = FileSystemObject(name)
        self._action_manager = FileSystemObjectManager("actions", Action, FileSystemAction, self)
        self._action_manager = FileSystemObjectManager("entities", Entity, FileSystemEntity, self)
        self._action_manager = FileSystemObjectManager("templates", Template, FileSystemTemplate, self)

    @property
    def actions(self):
        return self._action_manager

    @property
    def entities(self):
        return self._entities_manager

    @property
    def templates(self):
        return self._templates_manager

    @property
    def attributes(self):
        return self._attribute_manager


class FileSystemAction:
    def __init__(self, project, name):
        self._attribute_manager = FileSystemObject(project / 'actions' / name)
        self._message_manager = FileSystemObjectManager(project / 'actions' / name / "messages.yaml", Message, FileSystemMessage, self)

    def attributes(self):
        return self._attribute_manager

    def messages(self):
        return self._message_manager


class FileSystemEntity:
    def __init__(self, project, name):
        self._attribute_manager = FileSystemObject(project / 'entities' / name)
        self._message_manager = FileSystemObjectManager(project / 'entities' / name / "messages.yaml", Message, FileSystemMessage, self)

    def attributes(self):
        return self._attribute_manager

    def messages(self):
        return self._message_manager


class FileSystemModule:
    def __init__(self, module_type, project, name):
        assert module_type in ["action", "entity", "project"]
        self._content_manager = FileSystemObject(name / "modules")

    def contents(self):
        return self._content_manager


class FileSystemTemplate:
    def __init__(self, project, name):
        self._content_manager = FileSystemObject(project / 'templates' / name)

    def contents(self):
        return self._content_manager
