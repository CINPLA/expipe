import expipe
import os
import os.path as op
import collections
import datetime as dt
import quantities as pq
import numpy as np
import warnings
import copy
import abc
import pathlib
import re

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
        return self._backend.__getitem__(name)

    def __iter__(self):
        return self._backend.__iter__()

    def __len__(self):
        return self._backend.__len__()

    def __contains__(self, name):
        return self._backend.__contains__(name)

    def to_list(self):
        result = self._backend.to_list() or dict()
        return result


class MapManager:
    """
    Common class for all maps of objects, such as
    actions, modules, entities, templates, etc.
    """
    def __init__(self, backend):
        self._backend = backend

    def __getitem__(self, name):
        return self._backend.__getitem__(name)

    def __iter__(self):
        return self._backend.__iter__()

    def __len__(self):
        return self._backend.__len__()

    def __contains__(self, name):
        return self._backend.__contains__(name)

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    # def to_dict(self):
        # result = self._backend.contents.get() or dict()
        # return result

class ExpipeObject:
    """
    Parent class for expipe Project and expipe Action objects
    """
    def __init__(self, object_id, backend):
        self.id = object_id
        self._backend = backend

    @property
    def modules(self):
        return MapManager(self._backend.modules)

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

    def create_module(self, name=None, template=None, contents=None, overwrite=False):
        """
        Create and return a module. Fails if the target name already exists.
        """
        # TODO: what if both content and template is given, and also name?
        if name is None:
            name, contents = self._load_template(template)
        if name in self._backend.modules and not overwrite:
            raise NameError(
                "Module " + name + " already exists in " + self.id +
                ". use overwrite")

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
        if isinstance(self, Project):
            project = self
        elif isinstance(self, (Entity, Action)):
            project = self.project
        else:
            raise ValueError('Someting went wrong, unable to get project.')
        contents = project.templates[template].to_dict()
        name = contents.get('identifier')
        if name is None:
            raise ValueError('Template "' + template + '" has no identifier.')
        return name, contents

    def _create_module(self, name, contents):
        if not isinstance(contents, (dict, list, np.ndarray)):
            raise TypeError('Contents expected "dict" or "list" got "' +
                            str(type(contents)) + '".')
        self._backend.modules[name] = contents
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

    def get_action(self, name):
        warnings.warn(
            "`project.get_action(name)` is deprecated, please use `project.actions[name]` instead",
            DeprecationWarning)
        return self.actions[name]

    @property
    def actions(self):
        return MapManager(self._backend.actions)

    def _create_action(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self._backend.actions[name] = {"registered": dtime}
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
            raise NameError(
                "Action " + name + " already exists in " + self.id +
                ". use overwrite")

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
        return MapManager(self._backend.entities)

    def _create_entity(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self._backend.entities[name] = {"registered": dtime}
        return self.entities[name]

    def require_entity(self, name):
        """
        Get an entity, creating it if it doesn’t exist.
        """
        if name in self.entities:
            return self.entities[name]

        return self._create_entity(name)

    def create_entity(self, name, overwrite=False):
        """
        Create and return an entity. Fails if the target name already exists.
        """
        if name in self.entities:
            raise NameError(
                "Entity " + name + " already exists in " + self.id +
                ". use overwrite")

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
        return MapManager(self._backend.templates)

    def _create_template(self, name, contents):
        dtime = dt.datetime.today().strftime(datetime_format)
        contents.update({"registered": dtime})
        assert 'identifier' in contents
        self._backend.templates[name] = contents
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
            raise NameError(
                "Template " + name + " already exists in " + self.id +
                ". use overwrite")

        return self._create_template(name, contents)

    def delete_template(self, name):
        """
        Delete an template. Fails if the target name does not exists.
        """
        template = self.templates[name]
        self._backend.templates.delete(name)
        del template


class Entity(ExpipeObject):
    """
    Expipe entity object
    """
    def __init__(self, entity_id, backend):
        super(Entity, self).__init__(
            entity_id,
            backend
        )

    @property
    def messages(self):
        return MapManager(self._backend.messages)

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

        if datetime_key_str in self._backend.messages:
            raise KeyError("Message with the same datetime already exists '{}'".format(datetime_key_str))

        self._backend.messages[datetime_key_str] = message
        return self._backend.messages[datetime_key_str]

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
        return dt.datetime.strptime(self._backend.attributes.get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
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


class Action(ExpipeObject):
    """
    Expipe action object
    """
    def __init__(self, action_id, backend):
        super(Action, self).__init__(
            action_id,
            backend
        )

    def get_module(self, name):
        warnings.warn(
            "The method`action.get_module(name)` is deprecated. "
            "Please use `action.modules[name]` instead", DeprecationWarning)
        return self.modules[name]

    @property
    def messages(self):
        return MapManager(self._backend.messages)

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

        if datetime_key_str in self._backend.messages:
            raise KeyError("Message with the same datetime already exists '{}'".format(datetime_key_str))

        self._backend.messages[datetime_key_str] = message
        return self._backend.messages[datetime_key_str]

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
    def datetime(self):
        return dt.datetime.strptime(self._backend.attributes.get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
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

    def require_filerecord(self, class_type=None, name=None):
        class_type = class_type or Filerecord
        return class_type(self, name)


class Module:
    def __init__(self, module_id, backend):
        self.id = module_id
        self._backend = backend

    def __getitem__(self, name):
        return Module(name, self._backend)

    def __setitem__(self, name, contents):
        self._backend.set(name=name, value=contents)

    def to_dict(self):
        result = self._get_module_content() or {}
        return result

    def to_json(self, fname=None):
        import json
        fname = fname or self.id
        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError('The filename "' + fname +
                                  '" exists, choose another')
        with open(fname, 'w') as outfile:
            json.dump(self.to_dict(), outfile,
                      sort_keys=True, indent=4)

    def keys(self):
        result = self._get_module_content() or {}
        return result.keys()

    def items(self):
        result = self._get_module_content() or {}
        return result.items()

    def values(self):
        result = self._get_module_content()
        if result is None:
            result = dict()
        return result.values()

    def _get_module_content(self):
        result = self._backend.contents.get()
        # if isinstance(result, list):
            # if len(result) > 0:
                # raise TypeError('Got nonempty list, expected dict')
            # result = None
        return result


class Template:
    def __init__(self, template_id, backend):
        self.id = template_id
        self._backend = backend

    def to_dict(self):
        result = self._get_template_content() or {}
        return result

    def to_json(self, fname=None):
        import json
        fname = fname or self.id
        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError('The filename "' + fname +
                                  '" exists, choose another')
        with open(fname, 'w') as outfile:
            json.dump(self.to_dict(), outfile,
                      sort_keys=True, indent=4)

    def keys(self):
        result = self._get_template_content() or {}
        return result.keys()

    def items(self):
        result = self._get_template_content() or {}
        return result.items()

    def values(self):
        result = self._get_template_content()
        if result is None:
            result = dict()
        return result.values()

    def _get_template_content(self):
        result = self._backend.contents.get()
        if isinstance(result, list):
            if len(result) > 0:
                raise TypeError('Got nonempty list, expected dict')
            result = None
        return result


class Message:
    """
    Message class
    """
    def __init__(self, message_id, backend):
        self.id = message_id
        self._backend = backend

    @property
    def name(self):
        return self._name

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

    def to_dict(self):
        content = self._backend.contents.get()
        if content:
            content['datetime'] = dt.datetime.strptime(content['datetime'],
                                                       datetime_format)
        return content


class Filerecord:
    def __init__(self, action, filerecord_id=None):
        self.id = filerecord_id or "main"  # oneliner hack by Mikkel
        self.action = action

        # TODO make into properties/functions in case settings change
        self.exdir_path = op.join(
            action.project.id, action.id, self.id + ".exdir")
        if 'data_path' in expipe.settings:
            self.local_path = op.join(expipe.settings["data_path"],
                                      self.exdir_path)
        else:
            self.local_path = None
        if 'server_path' in expipe.settings:
            self.server_path = op.join(expipe.settings['server']["data_path"],
                                       self.exdir_path)
        else:
            self.server_path = None

        # TODO if not exists and not required, return error
        ref_path = "/".join(["files", action.project.id, action.id])
        self._backend = FirebaseObject(ref_path)
        if not self._backend.contents.get(self.id):
            self._backend.update(self.id, {"path": self.exdir_path})


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

    def __getitem__(self, args):
        data = self.data or []
        return data[args]

    def __len__(self):
        data = self.data or []
        return len(data)

    def __contains__(self, value):
        value = self.dtype_manager(value)
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
        if value is None or self.dtype is None:
            return
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

def load_file_system(config_name=None, root=None):
    if not config_name and not root:
        root = pathlib.Path.cwd()
    elif config_name:
        config = expipe.config._load_config_by_name("file_system", config_name)
        config = expipe.config._extend_config(config)
        root = config["file_system"]["root"]

    backend = expipe.backends.filesystem.FileSystemBackend(root=root)
    return Database(backend)

def load_firebase(config_name=None):
    config = expipe.config._load_config_by_name("firebase", config_name)
    config = expipe.config._extend_config(config)
    # TODO It would be better only to pass the necessary information to FirebaseBackend
    # firebase_config = config["firebase"]
    # email = firebase_config["email"]
    # password = firebase_config["password"]
    # config_details = firebase_config["config"]
    backend = expipe.backends.firebase.FirebaseBackend(config)
    return Database(backend)

# Deprecated API

def require_project(name):
    warnings.warn(
        "The function `require_project` is deprecated."
        "Please use `load_firebase` or `load_file_system`.",
        DeprecationWarning)

    database = load_firebase(pathlib.Path.home() / ".config" / "expipe" / "config.yaml")
    return database.require_project(name)

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
