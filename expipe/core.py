import os
import os.path as op
import requests
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


######################################################################################################
# Managers
######################################################################################################
class ActionManager:
    """
    Manager class for retrieving actions in a project
    """
    def __init__(self, project):
        self.project = project
        self._db = FirebaseBackend('/actions/' + project.id)

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Action '{}' does not exist".format(name))
        return self._get(name)

    def _get(self, name):
        return Action(project=self.project, action_id=name)

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        return name in (self._db.get(shallow=True) or [])

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def to_dict(self):
        result = self._db.get() or dict()
        return result


class EntityManager:
    """
    Manager class for retrieving entities in a project
    """
    def __init__(self, project):
        self.project = project
        self._db = FirebaseBackend('/entities/' + project.id)

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Entity '{}' does not exist".format(name))
        return self._get(name)

    def _get(self, name):
        return Entity(project=self.project, entity_id=name)

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        return name in (self._db.get(shallow=True) or [])

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def to_dict(self):
        result = self._db.get() or dict()
        return result


class TemplateManager:
    """
    Manager class for retrieving entities in a project
    """
    def __init__(self, project):
        self.project = project
        self._db = FirebaseBackend('/templates/' + project.id)

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Template '{}' does not exist".format(name))
        return self._get(name)

    def _get(self, name):
        return Template(project=self.project, template_id=name)

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        return name in (self._db.get(shallow=True) or [])

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def to_dict(self):
        result = self._db.get() or dict()
        return result


class ModuleManager:
    """
    Manager class for retrieving modules in a project, entity or an action
    """
    def __init__(self, parent):
        if isinstance(parent, Action):
            module_path = '/'.join(['action_modules', parent.project.id, parent.id])
        elif isinstance(parent, Entity):
            module_path = '/'.join(['entity_modules', parent.project.id, parent.id])
        elif isinstance(parent, Project):
            module_path = '/'.join(['project_modules', parent.id])
        else:
            raise TypeError("Parent of type '{}' cannot have modules.".format(type(parent)))

        self.parent = parent
        self._db = FirebaseBackend(module_path)

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Module '{}' does not exist".format(name))
        return self._get(name)

    def _get(self, name):
        return Module(parent=self.parent, module_id=name)

    def __iter__(self):
        keys = self._db.get(shallow=True) or []
        for key in keys:
            yield key

    def __len__(self):
        keys = self._db.get(shallow=True) or []
        return len(keys)

    def __contains__(self, name):
        return name in (self._db.get(shallow=True) or [])

    def items(self):
        return collections.abc.ItemsView(self)

    def keys(self):
        return collections.abc.KeysView(self)

    def values(self):
        return collections.abc.ValuesView(self)

    def to_dict(self):
        d = {}
        for name in self.keys():
            d[name] = self[name].to_dict()
        return d

    def to_json(self, fname=None):
        warnings.warn("module_manager.to_json() is deprecated. Will be removed in next version!")
        import json
        fname = fname or self.parent.id

        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError("The filename '{}' exists, choose another".format(fname))

        vprint("Saving module '{}' to '{}'".format(self.parent.id, fname))
        with open(fname, 'w') as outfile:
            json.dump(self.to_dict(), outfile, sort_keys=True, indent=4)


class MessageManager:
    """
    Manager class for messages in an action or entity
    """
    def __init__(self, parent):
        if isinstance(parent, Action):
            path = "/".join(["action_messages", parent.project.id, parent.id])
        elif isinstance(parent, Entity):
            path = "/".join(["entity_messages", parent.project.id, parent.id])
        else:
            raise TypeError(
                "Parent must be of type Action, given type" +
                " {}".format(type(parent)))
        self._db = FirebaseBackend(path)
        self.parent = parent

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Action '{}' does not exist".format(name))
        return self._get(name)

    def __contains__(self, item):
        return item in [a.to_dict() for a in self]

    def __iter__(self):
        keys = self.keys()
        for key in keys:
            yield Message(parent=self.parent, message_id=key)

    def __len__(self):
        return len(self.keys())

    def _get(self, name):
        return Message(parent=self.parent, message_id=name)

    def keys(self):
        keys = self._db.get(shallow=True) or []
        return keys


######################################################################################################
# Main classes
######################################################################################################
class ExpipeObject:
    """
    Parent class for expipe Project and expipe Action objects
    """
    def __init__(self, object_id, db_modules):
        self.id = object_id
        self._db_modules = db_modules

    @property
    def modules(self):
        return ModuleManager(self)

    def require_module(self, name=None, template=None, contents=None, overwrite=False):
        """
        Get a module, creating it if it doesn’t exist.
        """
        # TODO: what if both content and template is given, and also name?

        if name is None:
            name, contents = self._load_template(template)
        exists = self._db_modules.exists(name)
        if exists and contents is None:
            return self.modules._get(name)
        elif exists and contents is not None:
            if overwrite is False:
                raise NameError(
                    "Module " + name + " already exists in " + self.id +
                    ". use overwrite")
        return self._create_module(
            name=name,
            contents=contents
        )

    def create_module(self, name=None, template=None, contents=None):
        """
        Create and return a module. Fails if the target name already exists.
        """
        # TODO: what if both content and template is given, and also name?
        if name is None:
            name, contents = self._load_template(template)
        exists = self._db_modules.exists(name)
        if exists:
            raise NameError(
                "Module " + name + " already exists in " + self.id + ".")

        return self._create_module(
            name=name,
            contents=contents
        )

    def get_module(self, name):
        """
        This function is deprecated.
        Get a module. Fails if the target name does not exists.
        """
        warnings.warn("object.get_module(name) is deprecated. Use object.modules[name] instead.")
        return self.modules[name]

    def delete_module(self, name):
        """
        Delete a module. Fails if the target name does not exists.
        """
        exists = self._db_modules.exists(name)
        if not exists:
            raise KeyError("Module {} does not exist in {}".format(name, self.id))
        self._db_modules.delete(name)

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
        module._db.set(name=None, value=contents)
        return module


class Project(ExpipeObject):
    """
    Expipe project object
    """
    def __init__(self, project_id):
        super(Project, self).__init__(
            object_id=project_id,
            db_modules=FirebaseBackend('/project_modules/' + project_id)
        )
        self._db_actions = FirebaseBackend('/actions/' + project_id)
        self._db_entities = FirebaseBackend('/entities/' + project_id)
        self._db_templates = FirebaseBackend('/templates/' + project_id)

    @property
    def actions(self):
        return ActionManager(self)

    def _create_action(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self._db_actions.set(name=name, value={"registered": dtime})
        return self.actions._get(name)

    def require_action(self, name):
        """
        Get an action, creating it if it doesn’t exist.
        """
        exists = self._db_actions.exists(name)
        if exists:
            return self.actions._get(name)

        return self._create_action(name)

    def create_action(self, name):
        """
        Create and return an action. Fails if the target name already exists.
        """
        exists = self._db_actions.exists(name)
        if exists:
            raise NameError("Action {} already exists in project {}".format(name, self.id))

        return self._create_action(name)

    def get_action(self, name):
        """
        This function is deprecated.
        Get an existing action. Fails if the target name does not exists.
        """
        warnings.warn("project.get_action(name) is deprecated. Use project.actions[name] instead.")
        return self.actions[name]

    def delete_action(self, name):
        """
        Delete an action. Fails if the target name does not exists.
        """
        action = self.actions[name]
        action.delete_messages()
        for module in list(action.modules.keys()):
            action.delete_module(module)
        self._db_actions.delete(name)
        del action

    @property
    def entities(self):
        return EntityManager(self)

    def _create_entity(self, name):
        dtime = dt.datetime.today().strftime(datetime_format)
        self._db_entities.set(name=name, value={"registered": dtime})
        return self.entities._get(name)

    def require_entity(self, name):
        """
        Get an entity, creating it if it doesn’t exist.
        """
        exists = self._db_entities.exists(name)
        if exists:
            return self.entities._get(name)

        return self._create_entity(name)

    def create_entity(self, name):
        """
        Create and return an entity. Fails if the target name already exists.
        """
        exists = self._db_entities.exists(name)
        if exists:
            raise NameError("Entity {} already exists in project {}".format(name, self.id))

        return self._create_entity(name)

    def get_entity(self, name):
        """
        This function is deprecated.
        Get an existing entity. Fails if the target name does not exists.
        """
        warnings.warn("project.get_entity(name) is deprecated. Use project.entities[name] instead.")
        return self.entities[name]

    def delete_entity(self, name):
        """
        Delete an entity. Fails if the target name does not exists.
        """
        entity = self.entities[name]
        entity.delete_messages()
        for module in list(entity.modules.keys()):
            entity.delete_module(module)
        self._db_entities.delete(name)
        del entity

    @property
    def templates(self):
        return TemplateManager(self)

    def _create_template(self, name, contents):
        dtime = dt.datetime.today().strftime(datetime_format)
        contents.update({"registered": dtime})
        assert 'identifier' in contents
        self._db_templates.set(name=name, value=contents)
        return self.templates._get(name)

    def require_template(self, name, contents=None, overwrite=False):
        """
        Get an template, creating it if it doesn’t exist.
        """
        exists = self._db_templates.exists(name)
        if exists and contents is None:
            return self.templates._get(name)
        elif exists and contents is not None:
            if overwrite is False:
                raise NameError(
                    "Template " + name + " already exists in " + self.id +
                    ". use overwrite")

        return self._create_template(name, contents)

    def create_template(self, name, contents):
        """
        Create and return an template. Fails if the target name already exists.
        """
        exists = self._db_templates.exists(name)
        if exists:
            raise NameError(
                "Template " + name + " already exists in " + self.id + ".")

        return self._create_template(name, contents)

    def delete_template(self, name):
        """
        Delete an template. Fails if the target name does not exists.
        """
        template = self.templates[name]
        self._db_templates.delete(name)
        del template


class Entity(ExpipeObject):
    """
    Expipe entity object
    """
    def __init__(self, project, entity_id):
        super(Entity, self).__init__(
            object_id=entity_id,
            db_modules=FirebaseBackend("/".join(["entity_modules", project.id, entity_id]))
        )
        self.project = project
        self._entity_dirty = True
        path = "/".join(["entities", self.project.id, self.id])
        messages_path = "/".join(["entity_messages", self.project.id, self.id])
        self._db = FirebaseBackend(path)
        self._db_messages = FirebaseBackend(messages_path)

    def _db_get(self, name):
        if self._entity_dirty:
            self._data = self._db.get()
            self._entity_dirty = False
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

        result = self._db_messages.push(message)
        return self.messages[result["name"]]

    def delete_messages(self):
        for message in self.messages:
            self._db_messages.delete(name=message.name)

    def _assert_message_dtype(self, text, user, datetime):
        _assert_message_text_dtype(text)
        _assert_message_user_dtype(user)
        _assert_message_datetime_dtype(datetime)

    @property
    def location(self):
        return self._db_get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('location', value)

    @property
    def type(self):
        return self._db_get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('type', value)

    @property
    def datetime(self):
        return dt.datetime.strptime(self._db_get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
        dtime = value.strftime(datetime_format)
        self._db.set('datetime', dtime)

    @property
    def users(self):
        return ProperyList(self._db, 'users', dtype=str, unique=True,
                           data=self._db_get('users'))

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._db.set('users', value)

    @property
    def tags(self):
        return ProperyList(self._db, 'tags', dtype=str, unique=True,
                           data=self._db_get('tags'))

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._db.set('tags', value)

    def require_filerecord(self, class_type=None, name=None):
        class_type = class_type or Filerecord
        return class_type(self, name)


class Action(ExpipeObject):
    """
    Expipe action object
    """
    def __init__(self, project, action_id):
        super(Action, self).__init__(
            object_id=action_id,
            db_modules=FirebaseBackend("/".join(["action_modules", project.id, action_id]))
        )
        self.project = project
        self._action_dirty = True
        path = "/".join(["actions", self.project.id, self.id])
        messages_path = "/".join(["action_messages", self.project.id, self.id])
        self._db = FirebaseBackend(path)
        self._db_messages = FirebaseBackend(messages_path)

    def _db_get(self, name):
        if self._action_dirty:
            self._data = self._db.get()
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

        result = self._db_messages.push(message)
        return self.messages[result["name"]]

    def delete_messages(self):
        for message in self.messages:
            self._db_messages.delete(name=message.name)

    def _assert_message_dtype(self, text, user, datetime):
        _assert_message_text_dtype(text)
        _assert_message_user_dtype(user)
        _assert_message_datetime_dtype(datetime)

    @property
    def location(self):
        return self._db_get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('location', value)

    @property
    def type(self):
        return self._db_get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('type', value)

    @property
    def entities(self):
        return ProperyList(self._db, 'entities', dtype=str, unique=True,
                           data=self._db_get('entities'))

    @entities.setter
    def entities(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._db.set('entities', value)

    @property
    def datetime(self):
        return dt.datetime.strptime(self._db_get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, dt.datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
        dtime = value.strftime(datetime_format)
        self._db.set('datetime', dtime)

    @property
    def users(self):
        return ProperyList(self._db, 'users', dtype=str, unique=True,
                           data=self._db_get('users'))

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._db.set('users', value)

    @property
    def tags(self):
        return ProperyList(self._db, 'tags', dtype=str, unique=True,
                           data=self._db_get('tags'))

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                            str([type(v) for v in value]))
        value = list(set(value))
        self._db.set('tags', value)

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
            path = '/'.join(['action_modules', parent.project.id,
                             parent.id, self.id])
        elif isinstance(parent, Project):
            path = '/'.join(['project_modules', parent.id, self.id])
        elif isinstance(parent, Entity):
            path = '/'.join(['entity_modules', parent.project.id,
                             parent.id, self.id])
        else:
            raise IOError('Parent of type "' + type(parent) +
                          '" cannot have modules.')
        self._db = FirebaseBackend(path)

    # TODO module reference id

    def to_dict(self):
        d = self._db.get()
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
        result = self._db.get()
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
        self._db = FirebaseBackend(path)

    def to_dict(self):
        d = self._db.get()
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
        result = self._db.get()
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
        self._db = FirebaseBackend(path)

    @property
    def name(self):
        return self._name

    @property
    def text(self):
        return self._db.get(name="text")

    @text.setter
    def text(self, value):
        _assert_message_text_dtype(value)
        self._db.set(name="text", value=value)

    @property
    def user(self):
        return self._db.get(name="user")

    @user.setter
    def user(self, value=None):
        value = value or expipe.settings.get("username")
        _assert_message_user_dtype(value)
        self._db.set(name="user", value=value)

    @property
    def datetime(self):
        value = self._db.get(name="datetime")
        return dt.datetime.strptime(value, datetime_format)

    @datetime.setter
    def datetime(self, value):
        _assert_message_datetime_dtype(value)
        value_str = dt.datetime.strftime(value, datetime_format)
        self._db.set(name="datetime", value=value_str)

    def to_dict(self):
        content = self._db.get()
        if content:
            content['datetime'] = dt.datetime.strptime(content['datetime'],
                                                       datetime_format)
        return content


######################################################################################################
# Backend
######################################################################################################
class AbstractBackend(abc.ABC):
    def __init__(self, path):
        self.path = path

    @abc.abstractmethod
    def exists(self, name=None):
        pass

    @abc.abstractmethod
    def get(self, name=None, shallow=False):
        pass

    @abc.abstractmethod
    def set(self, name, value=None):
        pass

    @abc.abstractmethod
    def push(self, value=None):
        pass

    @abc.abstractmethod
    def delete(self, name):
        pass

    @abc.abstractmethod
    def update(self, name, value=None):
        pass


class FirebaseBackend(AbstractBackend):
    def __init__(self, path):
        super(FirebaseBackend, self).__init__(
            path=path
        )
        self.id_token = None
        self.refresh_token = None
        self.token_expiration = dt.datetime.now()

    def ensure_auth(self):
        current_time = dt.datetime.now()
        api_key = expipe.settings["firebase"]["config"]["apiKey"]

        if self.id_token is not None and self.refresh_token is not None:
            if current_time + dt.timedelta(0, 10) < self.token_expiration and False:
                return
            auth_url = "https://securetoken.googleapis.com/v1/token?key={}".format(api_key)
            auth_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }

            response = requests.post(auth_url, json=auth_data)
            value = response.json()
            assert(response.status_code == 200)
            assert("errors" not in value)
            self.id_token = value["id_token"]
            self.refresh_token = value["refresh_token"]
            return

        auth_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={}".format(api_key)
        auth_data = {
            "email": expipe.settings["firebase"]["email"],
            "password": expipe.settings["firebase"]["password"],
            "returnSecureToken": True
        }
        response = requests.post(auth_url, json=auth_data)
        assert(response.status_code == 200)
        value = response.json()
        assert("errors" not in value)
        self.refresh_token = value["refreshToken"]
        self.id_token = value["idToken"]
        self.token_expiration = current_time + dt.timedelta(0, int(value["expiresIn"]))

    def build_url(self, name=None):
        if name is None:
            full_path = self.path
        else:
            full_path = "/".join([self.path, name])
        database_url = expipe.settings["firebase"]["config"]["databaseURL"]
        return "{database_url}/{name}.json?auth={id_token}".format(
            database_url=database_url,
            name=full_path,
            id_token=self.id_token
        )

    def exists(self, name=None):
        self.ensure_auth()
        value = self.get(name, shallow=True)
        if value is not None:
            return True
        else:
            return False

    def get(self, name=None, shallow=False):
        self.ensure_auth()
        url = self.build_url(name)
        if shallow:
            url += "&shallow=true"
        vprint("URL", url)
        response = requests.get(url)
        vprint("Get result", response.json())
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        value = convert_from_firebase(value)
        return value

    # def get_keys(self, name=None):
    #     return self.get(name, shallow=True)

    def set(self, name, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        vprint("URL", url)
        response = requests.put(url, json=value)
        vprint("Set result", response.json())
        assert(response.status_code == 200)
        value = response.json()
        if value is not None:
            assert("errors" not in value)

    def push(self, name=None, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        vprint("URL", url)
        response = requests.post(url, json=value)
        vprint("Push result", response.json())
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        return value

    def delete(self, name):
        db.child(self.path).child(name).set({}, user["idToken"])

    def update(self, name, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        value = convert_to_firebase(value)
        vprint("URL", url)
        response = requests.patch(url, json=value)
        vprint("Set result", response.json())
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        value = convert_from_firebase(value)
        return value


class Filerecord:
    def __init__(self, action, filerecord_id=None):
        self.id = filerecord_id or "main"  # oneliner hack by Mikkel
        self.action = action

        # TODO make into properties/functions in case settings change
        self.exdir_path = op.join(action.project.id, action.id,
                                  self.id + ".exdir")
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
        self._db = FirebaseBackend(ref_path)
        if not self._db.get(self.id):
            self._db.update(self.id, {"path": self.exdir_path})


class ProperyList:
    def __init__(self, db_instance, name, dtype=None, unique=False,
                 data=None):
        self._db = db_instance
        self.name = name
        self.dtype = dtype
        self.unique = unique
        self.data = data or self._db.get(self.name)

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
        self._db.set(self.name, data)

    def extend(self, value):
        data = self.data or []
        result = self.dtype_manager(value, iter_value=True)
        data.extend(result)
        if self.unique:
            data = list(set(data))
        self._db.set(self.name, data)

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
def convert_from_firebase(value):
    """
    Converts quantities back from dictionary
    """
    result = value
    if isinstance(value, dict):
        if "_force_dict" in value:
            del value["_force_dict"]
        if 'units' in value and "value" in value:
            value['unit'] = value['units']
            del(value['units'])
        if "unit" in value and "value" in value:
            if "uncertainty" in value:
                try:
                    result = pq.UncertainQuantity(value["value"],
                                                  value["unit"],
                                                  value["uncertainty"])
                except Exception:
                    pass
            else:
                try:
                    result = pq.Quantity(value["value"], value["unit"])
                except Exception:
                    pass
        else:
            try:
                for key, value in result.items():
                    result[key] = convert_from_firebase(value)
            except AttributeError:
                pass
    if isinstance(result, str):
        if result == 'NaN':
            result = np.nan
    elif isinstance(result, list):
        result = [v if v != 'NaN' else np.nan for v in result]
    return result


def convert_to_firebase(value):
    """
    Converts quantities to dictionary
    """
    if isinstance(value, dict):
        if all(isinstance(key, int) or (isinstance(key, str) and key.isnumeric()) for key in value):
            value["_force_dict"] = True
    if isinstance(value, np.ndarray) and not isinstance(value, pq.Quantity):
        if value.ndim >= 1:
            value = value.tolist()
    if isinstance(value, list):
        value = [convert_to_firebase(val) for val in value]

    result = value

    if isinstance(value, pq.Quantity):
        try:
            val = ['NaN' if np.isnan(r) else r for r in value.magnitude]
        except TypeError:
            val = value.magnitude.tolist()
        result = {"value": val,
                  "unit": value.dimensionality.string}
        if isinstance(value, pq.UncertainQuantity):
            assert(value.dimensionality == value.uncertainty.dimensionality)
            result["uncertainty"] = value.uncertainty.magnitude.tolist()
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
                new_key = convert_to_firebase(key)
                new_result[new_key] = convert_to_firebase(val)
            result = new_result
        except AttributeError:
            pass
    try:
        if not isinstance(value, list) and np.isnan(result):
            result = 'NaN'
    except TypeError:
        pass
    return result


def get_project(project_id):
    project_db = FirebaseBackend("/projects")
    existing = project_db.exists(project_id)
    if not existing:
        raise KeyError("Project " + project_id + " does not exist.")
    return Project(project_id)


def require_project(project_id):
    """Creates a new project with the provided id."""
    project_db = FirebaseBackend("/projects")
    existing = project_db.exists(project_id)
    registered = dt.datetime.today().strftime(datetime_format)
    if not existing:
        project_db.set(name=project_id, value={"registered": registered})

    return Project(project_id)


def delete_project(project_id, remove_all_childs=False):
    """Deletes a project named after the provided id."""
    project_db = FirebaseBackend("/projects")
    existing = project_db.exists(project_id)
    if not existing:
        raise NameError('Project "' + project_id + '" does not exist.')
    else:
        if remove_all_childs:
            project = Project(project_id)
            for action in list(project.actions.keys()):
                project.delete_action(action)
            for module in list(project.modules.keys()):
                project.delete_module(module)
            for entity in list(project.entities.keys()):
                project.delete_entity(entity)
            for template in list(project.templates.keys()):
                project.delete_template(template)
        project_db.delete(name=project_id)


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
