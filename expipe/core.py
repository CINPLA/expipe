import os
import os.path as op
import collections
import datetime as dt
import quantities as pq
import numpy as np
import warnings
import copy
import abc
import expipe

datetime_format = '%Y-%m-%dT%H:%M:%S'
verbose = False

def vprint(*arg):
    if verbose:
        print(*arg)


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

    def to_dict(self):
        result = self._backend.get() or dict()
        return result

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
        exists = self._backend.modules.exists(name)
        if exists and not overwrite:
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
        exists = self._backend.modules.exists(name)
        if not exists:
            raise KeyError("Module {} does not exist in {}".format(name, self.id))
        self._backend.modules.delete(name)

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
        module = Module(parent=self, module_id=name)

        if not isinstance(contents, (dict, list, np.ndarray)):
            raise TypeError('Contents expected "dict" or "list" got "' +
                            str(type(contents)) + '".')
        contents = convert_to_firebase(contents)
        module._backend.set(name=None, value=contents)
        return module


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
        action.delete_messages()
        for module in list(action.modules.keys()):
            action.delete_module(module)
        self._backend.actions.delete(name)
        del action

    @property
    def entities(self):
        return MapManager(self._backend.entities)

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
        entity.delete_messages()
        for module in list(entity.modules.keys()):
            entity.delete_module(module)

        # TODO could perhaps be del self.entities[name]?
        self._backend.entities.delete(name)
        del entity

    @property
    def templates(self):
        return TemplateManager(self)

    def _create_template(self, name, contents):
        dtime = dt.datetime.today().strftime(datetime_format)
        contents.update({"registered": dtime})
        assert 'identifier' in contents
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
            raise NameError(
                "Template " + name + " already exists in " + self.id +
                ". use overwrite")

        return self._create_template(name, contents)

    def delete_template(self, name):
        """
        Delete an template. Fails if the target name does not exists.
        """
        template = self.templates[name]

        # TODO perhaps change this to `del self.templates[name]`?
        self._backend.templates.delete(name)
        del template


class Entity(ExpipeObject):
    """
    Expipe entity object
    """
    def __init__(self, project, entity_id, backend):
        super(Entity, self).__init__(
            entity_id,
            backend
        )
        self.project = project

    @property
    def messages(self):
        # TODO Messages do not fit this pattern - they are a list, not a map
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

        result = self._backend_messages.push(message)
        return self.messages[result["name"]]

    def delete_messages(self):
        for message in self.messages:
            self._backend_messages.delete(name=message.name)

    def _assert_message_dtype(self, text, user, datetime):
        _assert_message_text_dtype(text)
        _assert_message_user_dtype(user)
        _assert_message_datetime_dtype(datetime)

    @property
    def location(self):
        return self._backend_get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.set('location', value)

    @property
    def type(self):
        return self._backend_get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.set('type', value)

    @property
    def datetime(self):
        return dt.datetime.strptime(self._backend_get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
        dtime = value.strftime(datetime_format)
        self._backend.set('datetime', dtime)

    @property
    def users(self):
        return ProperyList(self._backend, 'users', dtype=str, unique=True,
                           data=self._backend_get('users'))

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.set('users', value)

    @property
    def tags(self):
        return ProperyList(self._backend, 'tags', dtype=str, unique=True,
                           data=self._backend_get('tags'))

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.set('tags', value)


class Action(ExpipeObject):
    """
    Expipe action object
    """
    def __init__(self, project, action_id):
        super(Action, self).__init__(
            object_id=action_id,
            db_modules=FirebaseObject("/".join(["action_modules", project.id, action_id]))
        )
        self.project = project
        self._action_dirty = True
        path = "/".join(["actions", self.project.id, self.id])
        messages_path = "/".join(["action_messages", self.project.id, self.id])
        self._backend = FirebaseObject(path)
        self._backend_messages = FirebaseObject(messages_path)

    def _backend_get(self, name):
        if self._action_dirty:
            self._data = self._backend.get()
            self._action_dirty = False
        return self._data.get(name)

    @property
    def messages(self):
        return MessageManager(self)

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

        result = self._backend_messages.push(message)
        return self.messages[result["name"]]

    def delete_messages(self):
        for message in self.messages:
            self._backend_messages.delete(name=message.name)

    def _assert_message_dtype(self, text, user, datetime):
        _assert_message_text_dtype(text)
        _assert_message_user_dtype(user)
        _assert_message_datetime_dtype(datetime)

    @property
    def location(self):
        return self._backend_get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.set('location', value)

    @property
    def type(self):
        return self._backend_get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._backend.set('type', value)

    @property
    def entities(self):
        return ProperyList(self._backend, 'entities', dtype=str, unique=True,
                           data=self._backend_get('entities'))

    @entities.setter
    def entities(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.set('entities', value)

    @property
    def datetime(self):
        return dt.datetime.strptime(self._backend_get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
        dtime = value.strftime(datetime_format)
        self._backend.set('datetime', dtime)

    @property
    def users(self):
        return ProperyList(self._backend, 'users', dtype=str, unique=True,
                           data=self._backend_get('users'))

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.set('users', value)

    @property
    def tags(self):
        return ProperyList(self._backend, 'tags', dtype=str, unique=True,
                           data=self._backend_get('tags'))

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._backend.set('tags', value)

    def require_filerecord(self, class_type=None, name=None):
        class_type = class_type or Filerecord
        return class_type(self, name)


class Module:
    def __init__(self, parent, module_id):
        self.parent = parent
        if not isinstance(module_id, str):
            raise TypeError('Module name must be string')
        self.id = module_id
        if isinstance(parent, Action):
            self.path = '/'.join(['action_modules', parent.project.id,
                             parent.id, self.id])
        elif isinstance(parent, Project):
            self.path = '/'.join(['project_modules', parent.id, self.id])
        elif isinstance(parent, Entity):
            self.path = '/'.join(['entity_modules', parent.project.id,
                             parent.id, self.id])
        elif isinstance(parent, Module):
            self.path = '/'.join([parent.path, self.id])
        else:
            raise IOError(
                'Parent of type "' + type(parent) + '" cannot have modules.')
        self._backend = FirebaseObject(self.path)

    # TODO module reference id

    def __getitem__(self, name):
        return Module(self, name)

    def __setitem__(self, name, contents):
        contents = convert_to_firebase(contents)
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
        vprint('Saving module "' + self.id + '" to "' + fname + '"')
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
        result = self._backend.get()
        if isinstance(result, list):
            if len(result) > 0:
                raise TypeError('Got nonempty list, expected dict')
            result = None
        return result


class Template:
    def __init__(self, project, template_id):
        self.project = project
        if not isinstance(template_id, str):
            raise TypeError('Module name must be string')
        self.id = template_id
        if isinstance(project, Project):
            path = '/'.join(['templates', project.id, self.id])
        else:
            raise IOError('Parent of type "' + type(project) +
                          '" cannot have templates.')
        self._backend = FirebaseObject(path)

    def to_dict(self):
        d = self._backend.get()
        if d is None:
            return {}
        return d

    def to_json(self, fname=None):
        import json
        fname = fname or self.id
        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError('The filename "' + fname +
                                  '" exists, choose another')
        vprint('Saving template "' + self.id + '" to "' + fname + '"')
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
        result = self._backend.get()
        if isinstance(result, list):
            if len(result) > 0:
                raise TypeError('Got nonempty list, expected dict')
            result = None
        return result


class Message:
    """
    Message class
    """
    def __init__(self, parent, message_id):
        if not isinstance(message_id, str):
            raise TypeError('Module name must be string')

        if isinstance(parent, Action):
            path = '/'.join(
                ['action_messages', parent.project.id, parent.id, message_id])
        elif isinstance(parent, Entity):
            path = '/'.join(
                ['entity_messages', parent.project.id, parent.id, message_id])
        else:
            raise TypeError(
                "Parent must be of type 'Action' or 'Entity', given" +
                " type {}".format(type(parent)))

        self._name = message_id
        self.parent = parent
        self._backend = FirebaseObject(path)

    @property
    def name(self):
        return self._name

    @property
    def text(self):
        return self._backend.get(name="text")

    @text.setter
    def text(self, value):
        _assert_message_text_dtype(value)
        self._backend.set(name="text", value=value)

    @property
    def user(self):
        return self._backend.get(name="user")

    @user.setter
    def user(self, value=None):
        value = value or expipe.settings.get("username")
        _assert_message_user_dtype(value)
        self._backend.set(name="user", value=value)

    @property
    def datetime(self):
        value = self._backend.get(name="datetime")
        return dt.datetime.strptime(value, datetime_format)

    @datetime.setter
    def datetime(self, value):
        _assert_message_datetime_dtype(value)
        value_str = dt.datetime.strftime(value, datetime_format)
        self._backend.set(name="datetime", value=value_str)

    def to_dict(self):
        content = self._backend.get()
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
        if not self._backend.get(self.id):
            self._backend.update(self.id, {"path": self.exdir_path})


class ProperyList:
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


######################################################################################################
# utilities
######################################################################################################
# Entry API

def _discover_backend(backend):
    if not backend:
        # TODO replace with some type of default backend discovery
        backend = FirebaseBackend()
    return backend

def projects():
    backend = _discover_backend(backend)
    return MapManager(backend.project_manager())

def get_project(project_id, backend=None):
    backend = _discover_backend(backend)

    existing = backend.projects.exists(project_id)

    if not existing:
        raise KeyError("Project " + project_id + " does not exist.")

    return Project(project_id, backend.projects.get(project_id))


def require_project(project_id, backend=None):
    """Creates a new project with the provided id if it does not already exist."""
    backend = _discover_backend(backend)

    if project_id not in backend.projects:
        registered = dt.datetime.today().strftime(datetime_format)
        backend.create_project(project_id, contents={"registered": registered})

    return Project(project_id, backend)


def delete_project(project_id, remove_all_childs=False, backend=None):
    """Deletes a project named after the provided id."""
    backend = _discover_backend(backend)

    existing = backend.projects.exists(project_id)

    if not existing:
        raise NameError('Project "' + project_id + '" does not exist.')
    else:
        if remove_all_childs:
            project = Project(project_id, backend)

            for action in list(project.actions.keys()):
                project.delete_action(action)
            for module in list(project.modules.keys()):
                project.delete_module(module)
            for entity in list(project.entities.keys()):
                project.delete_entity(entity)
            for template in list(project.templates.keys()):
                project.delete_template(template)

        project_backend.delete_project(name=project_id)


def load_database(backend):
    database = None
    return database


######################################################################################################
# Helpers
######################################################################################################
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
