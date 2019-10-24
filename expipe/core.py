from . import config
from . import widgets
from .widgets import display
import expipe
import collections.abc
import datetime as dt
import numpy as np
import warnings
import pathlib
import abc
import IPython.display as ipd
try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml

datetime_format = '%Y-%m-%dT%H:%M:%S'
datetime_key_format = '%Y%m%dT%H%M%S'
verbose = False


class ListManager:
    """
    Common class for lists of objects, such as messages.
    """
    def __init__(self, backend):
        self._backend = backend

    def __getitem__(self, index):
        return self._backend.__getitem__(index)

    def __iter__(self):
        return self._backend.__iter__()

    def __len__(self):
        return self._backend.__len__()

    def __contains__(self, name):
        return self._backend.__contains__(name)

    def to_list(self):
        result = self._backend.to_list() or dict()
        return result


def _assert_name_type(name):
    if not isinstance(name, (str, int)):
        raise TypeError(
            'Expected "name" to be of type "str" or "int" got {}'.format(type(name)))
    if name == '':
        raise ValueError('Argument "name" cannot be an empty string')


class MapManager:
    """
    Common class for all maps of objects, such as
    actions, modules, entities, templates, etc.
    """
    def __init__(self, backend):
        self._backend = backend

    def __eq__(self, other):
        return self._backend.__eq__(other)

    def __getitem__(self, name):
        _assert_name_type(name)
        return self._backend.__getitem__(name)

    def __setitem__(self, name, value):
        _assert_name_type(name)
        return self._backend.__setitem__(name, value)

    def __iter__(self):
        return self._backend.__iter__()

    def __len__(self):
        return self._backend.__len__()

    def __contains__(self, name):
        _assert_name_type(name)
        return self._backend.__contains__(name)

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def _ipython_key_completions_(self):
        return self.keys()

    @property
    def contents(self):
        if hasattr(self._backend, 'contents'):
            return self._backend.contents
        else:
            name = self._backend.__class__.__name__
            raise AttributeError('{} has no attribute "contents"'.format(name))


class Modules(MapManager):
    def __init__(self, object, backend):
        super(Modules, self).__init__(backend=backend)
        self.object = object

    def _ipython_display_(self):
        ipd.display(widgets.display.modules_view(self.object))


class Actions(MapManager):
    def __init__(self, object, backend):
        super(Actions, self).__init__(backend=backend)
        self.object = object

    def _ipython_display_(self):
        ipd.display(widgets.display.actions_view(self.object))


class Entities(MapManager):
    def __init__(self, object, backend):
        super(Entities, self).__init__(backend=backend)
        self.object = object

    def _ipython_display_(self):
        ipd.display(widgets.display.entities_view(self.object))


class Templates(MapManager):
    def __init__(self, object, backend):
        super(Templates, self).__init__(backend=backend)
        self.object = object

    def _ipython_display_(self):
        ipd.display(widgets.display.templates_view(self.object))


class Messages(MapManager):
    def __init__(self, object, backend):
        super(Messages, self).__init__(backend=backend)
        self.object = object

    def _ipython_display_(self):
        ipd.display(widgets.display.messages_view(self.object))


class ExpipeObject:
    """
    Parent class for expipe Project and expipe Action objects
    """
    def __init__(self, object_id, backend):
        self.id = object_id
        self._backend = backend

    @property
    def modules(self):
        return Modules(self, self._backend.modules)

    def require_module(self, name=None, template=None, contents=None):
        """
        Get a module, creating it if it doesn’t exist.
        """
        # TODO: what if both content and template is given, and also name?

        if name is None:
            name, contents = self._load_template(template)
        if name in self.modules:
            return self.modules[name]
        return self._create_module(
            name=name,
            contents=contents
        )

    def create_module(self, name=None, template=None, contents=None):
        """
        Create and return a module. Fails if the target name already exists.
        """
        if template is not None:
            assert contents is None
            _name, contents = self._load_template(template)
            if name is None:
                name = _name
        if name in self.modules:
            raise KeyError(
                "Module " + name + " already exists in " + self.id + ".")

        return self._create_module(
            name=name,
            contents=contents
        )

    def delete_module(self, name):
        """
        Delete a module. Fails if the target name does not exists.
        """
        module = self.modules[name]
        self._backend.modules.delete(name)
        del module

    def _load_template(self, template):
        contents = self._backend.templates[template].contents
        name = contents.get('identifier')
        if name is None:
            raise ValueError('Template "' + template + '" has no identifier.')
        return name, contents

    def _create_module(self, name, contents):
        if not isinstance(contents, (dict, list, np.ndarray)):
            raise TypeError('Contents expected "dict" or "list" got "' +
                            str(type(contents)) + '".')
        self.modules[name] = contents
        return self.modules[name]


class Project(ExpipeObject):
    """
    Expipe project object
    """
    def __init__(self, object_id, backend):
        super(Project, self).__init__(
            object_id,
            backend
        )

    @property
    def config(self):
        return self._backend.config

    def _ipython_display_(self):
        ipd.display(widgets.display.display_dict_html(self.config))

    @property
    def actions(self):
        return Actions(self, self._backend.actions)

    def _create_action(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self.actions[name] = {"registered": dtime}
        return self.actions[name]

    def require_action(self, name):
        """
        Get an action, creating it if it doesn’t exist.
        """
        if name in self.actions:
            return self.actions[name]

        return self._create_action(name)

    def create_action(self, name):
        """
        Create and return an action. Fails if the target name already exists.
        """
        if name in self.actions:
            raise KeyError(
                "Action " + name + " already exists in " + self.id + ".")

        return self._create_action(name)

    def delete_action(self, name):
        """
        Delete an action. Fails if the target name does not exists.
        """
        action = self.actions[name]
        action = self._backend.actions.delete(name)
        del action

    @property
    def entities(self):
        return Entities(self, self._backend.entities)

    def _create_entity(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self.entities[name] = {"registered": dtime}
        return self.entities[name]

    def require_entity(self, name):
        """
        Get an entity, creating it if it doesn’t exist.
        """
        if name in self.entities:
            return self.entities[name]

        return self._create_entity(name)

    def create_entity(self, name):
        """
        Create and return an entity. Fails if the target name already exists.
        """
        if name in self.entities:
            raise KeyError(
                "Entity " + name + " already exists in " + self.id + ".")

        return self._create_entity(name)

    def delete_entity(self, name):
        """
        Delete an entity. Fails if the target name does not exists.
        """
        entity = self.entities[name]
        action = self._backend.entities.delete(name)
        del entity

    @property
    def templates(self):
        return Templates(self, self._backend.templates)

    def _create_template(self, name, contents):
        dtime = dt.datetime.today().strftime(datetime_format)
        contents.update({"registered": dtime})
        if not 'identifier' in contents:
            raise ValueError('Template contents must contain "identifier"')
        self.templates[name] = contents
        return self.templates[name]

    def require_template(self, name, contents=None):
        """
        Get an template, creating it if it doesn’t exist.
        """
        if name in self.templates:
            return self.templates[name]

        return self._create_template(name, contents)

    def create_template(self, name, contents):
        """
        Create and return an template. Fails if the target name already exists.
        """
        if name in self.templates:
            raise KeyError(
                "Template " + name + " already exists in " + self.id + ".")

        return self._create_template(name, contents)

    def delete_template(self, name):
        """
        Delete an template. Fails if the target name does not exists.
        """
        template = self.templates[name]
        self._backend.templates.delete(name)
        del template

    @property
    def path(self):
        return self._backend.path


class ExpipeSubObject(ExpipeObject):
    def __init__(self, object_id, backend):
        super(ExpipeSubObject, self).__init__(
            object_id,
            backend
        )
    @property
    def messages(self):
        return Messages(self, self._backend.messages)

    def create_message(self, text, user=None, datetime=None):
        datetime = datetime or dt.datetime.now()
        user = user or expipe.settings.get("username")

        self._assert_message_dtype(text=text, user=user, datetime=datetime)

        datetime_str = dt.datetime.strftime(datetime, datetime_format)
        message = {
            "text": text,
            "user": user,
            "datetime": datetime_str
        }
        datetime_key_str = dt.datetime.strftime(datetime, datetime_key_format)

        if datetime_key_str in self.messages:
            raise KeyError("Message with the same datetime already exists '{}'".format(datetime_key_str))

        self.messages[datetime_key_str] = message
        return self.messages[datetime_key_str]

    def delete_messages(self):
        for message in self.messages:
            self._backend.messages.delete(name=message)

    def _assert_message_dtype(self, text, user, datetime):
        _assert_message_text_dtype(text)
        _assert_message_user_dtype(user)
        _assert_message_datetime_dtype(datetime)

    @property
    def location(self):
        return self._backend.attributes.get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.attributes.set('location', value)

    @property
    def type(self):
        return self._backend.attributes.get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.attributes.set('type', value)

    @property
    def datetime(self):
        dtime = self._backend.attributes.get('datetime')
        if dtime is None:
            return None
        try:
            return dt.datetime.strptime(dtime, datetime_format)
        except Exception as e:
            raise Exception(
                '"{}" "{}": "{}"'.format(self.__class__.__name__, self.id, e))

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError(
                'Expected "datetime" got "' + str(type(value)) + '".')
        dtime = value.strftime(datetime_format)
        self._backend.attributes.set('datetime', dtime)

    @property
    def users(self):
        return PropertyList(self._backend.attributes, 'users', dtype=str, unique=True,
                           data=self._backend.attributes.get('users'))

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.attributes.set('users', value)

    @property
    def tags(self):
        return PropertyList(self._backend.attributes, 'tags', dtype=str, unique=True,
                           data=self._backend.attributes.get('tags'))

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.attributes.set('tags', value)

    @property
    def attributes(self):
        return self._backend.attributes.get()

    @property
    def path(self):
        return self._backend.path


class Entity(ExpipeSubObject):
    """
    Expipe entity object
    """
    def __init__(self, entity_id, backend):
        super(Entity, self).__init__(
            entity_id,
            backend
        )


class Action(ExpipeSubObject):
    """
    Expipe action object
    """
    def __init__(self, action_id, backend):
        super(Action, self).__init__(
            action_id,
            backend
        )

    @property
    def entities(self):
        return PropertyList(self._backend.attributes, 'entities', dtype=str, unique=True,
                           data=self._backend.attributes.get('entities'))

    @entities.setter
    def entities(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.attributes.set('entities', value)

    @property
    def data(self):
        return MapManager(self._backend.data)

    def data_path(self, key=None):
        return self._backend.data_path(key)


class Module(MapManager):
    """
    Module
    """
    def __init__(self, module_id, backend):
        super(Module, self).__init__(backend=backend)
        self.id = module_id


class Template(MapManager):
    def __init__(self, template_id, backend):
        super(Template, self).__init__(backend=backend)
        self.id = template_id


class Message:
    """
    Message class
    """
    def __init__(self, message_id, backend):
        self.id = message_id
        self._backend = backend

    @property
    def text(self):
        return self._backend.contents.get(name="text")

    @text.setter
    def text(self, value):
        _assert_message_text_dtype(value)
        self._backend.contents.set(name="text", value=value)

    @property
    def user(self):
        return self._backend.contents.get(name="user")

    @user.setter
    def user(self, value=None):
        value = value or expipe.settings.get("username")
        _assert_message_user_dtype(value)
        self._backend.contents.set(name="user", value=value)

    @property
    def datetime(self):
        value = self._backend.contents.get(name="datetime")
        return dt.datetime.strptime(value, datetime_format)

    @datetime.setter
    def datetime(self, value):
        _assert_message_datetime_dtype(value)
        value_str = dt.datetime.strftime(value, datetime_format)
        self._backend.contents.set(name="datetime", value=value_str)

    @property
    def contents(self):
        content = self._backend.contents.get()
        if content:
            content['datetime'] = dt.datetime.strptime(content['datetime'],
                                                       datetime_format)
        return content


class PropertyList:
    def __init__(self, db_instance, name, dtype=None, unique=False,
                 data=None):
        self._backend = db_instance
        self.name = name
        self.dtype = dtype
        self.unique = unique
        self.data = data or self._backend.get(self.name)

    def __iter__(self):
        data = self.data or []
        for d in data:
            yield d

    def __eq__(self, other):
        data = self.data or []
        return data == other

    def __getitem__(self, args):
        data = self.data or []
        return data[args]

    def __len__(self):
        data = self.data or []
        return len(data)

    def __contains__(self, value):
        value = self.dtype_manager(value)
        if not self.data:
            return False
        return value in self.data

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return self.data.__repr__()

    def append(self, value):
        data = self.data or []
        result = self.dtype_manager(value)
        data.append(result)
        if self.unique:
            data = list(set(data))
        self._backend.set(self.name, data)

    def extend(self, value):
        data = self.data or []
        result = self.dtype_manager(value, iter_value=True)
        data.extend(result)
        if self.unique:
            data = list(set(data))
        self._backend.set(self.name, data)

    def dtype_manager(self, value, iter_value=False, retrieve=False):
        if iter_value:
            if not all(isinstance(v, self.dtype) for v in value):
                raise TypeError('Expected ' + str(self.dtype) + ' got ' +
                                str([type(v) for v in value]))
        else:
            if not isinstance(value, self.dtype):
                raise TypeError('Expected ' + str(self.dtype) + ' got ' +
                                str(type(value)))

        return value


# Entry API
class Database:
    def __init__(self, backend):
        self._backend = backend

    def get_project(self, name):
        if not self._backend.exists(name):
            raise KeyError("Project does not exist.")

        return self._backend.get_project(name)


    def create_project(self, name):
        registered = dt.datetime.today().strftime(datetime_format)
        return self._backend.create_project(name, contents={"registered": registered})


    def require_project(self, name):
        """Creates a new project with the provided id if it does not already exist."""
        if self._backend.exists(name):
            return self.get_project(name)
        else:
            return self.create_project(name)


    def delete_project(self, name, remove_all_children=None):
        if self._backend.exists(name):
            self._backend.delete_project(name, remove_all_children=remove_all_children)
        else:
            raise KeyError("Project does not exist.")

# Entry API
def get_project(path, name=None):
    import expipe.backends.filesystem
    path = pathlib.Path(path).resolve()

    name = name or path.stem

    global_config = config.settings.copy()

    local_config_path = path / "expipe.yaml"
    if not local_config_path.exists():
        raise KeyError("Could not find '{}'.".format(local_config_path))

    local_config = config._load_config(local_config_path)

    try:
        project = local_config['project']
        project_config = config._load_config_by_name(project)
    except KeyError:
        warnings.warn(
            "Project has no name. Please add 'project: name' to" +
            " '{}'.".format(local_config_path))
        project = "unnamed"
        project_config = {}

    if name is not None and name != project:
        warnings.warn(
            "Requested project with name " +
            "'{}', but found '{}'".format(name, project))

    final_config = config._merge_config(
        global_config, project_config, local_config)
    backend = expipe.backends.filesystem.FileSystemProject(path, final_config)
    return Project(project, backend)


def create_project(path, name=None, init=False):
    path = pathlib.Path(path).resolve()

    name = name or path.stem

    # see if we are in a project directory
    if config._is_in_project(path):
        raise KeyError(
            'You are not allowed to create a project inside an existing' +
            ' project')

    path.mkdir(parents=True, exist_ok=init)

    local_config_path = path / "expipe.yaml"
    local_config = {
        "database_version": 2,
        "type": "project",
        "project": name
    }

    with local_config_path.open('w') as f:
        yaml.dump(local_config, f)

    return get_project(path)


def require_project(path, name=None):
    path = pathlib.Path(path).resolve()

    local_config_path = path / "expipe.yaml"

    if local_config_path.exists():
        return get_project(path, name)
    elif path.exists():
        raise FileExistsError("Path already exists, but is not expipe project: '{}'".format(path))
    else:
        return create_project(path, name)


# Helpers

def _assert_message_text_dtype(text):
    if not isinstance(text, str):
        raise TypeError("Text must be of type 'str', not {} {}".format(type(text), text))


def _assert_message_user_dtype(user):
    if not isinstance(user, str):
        raise TypeError("User must be of type 'str', not {} {}".format(type(user), user))


def _assert_message_datetime_dtype(datetime):
    if not isinstance(datetime, dt.datetime):
        raise TypeError("Datetime must be of type 'datetime', not {} {}".format(type(datetime),
                                                                                datetime))
