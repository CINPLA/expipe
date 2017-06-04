from datetime import datetime
import os
import os.path as op
import pyrebase
import configparser
import quantities as pq
import numpy as np
import warnings
import expipe


datetime_format = '%Y-%m-%dT%H:%M:%S'


class DictDiffer(object):
    """
    A dictionary difference calculator
    Originally posted as:
    http://stackoverflow.com/questions/1165352/fast-comparison-between-two-python-dictionary/1165552#1165552

    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.current_keys, self.past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
        ]
        self.intersect = self.current_keys.intersection(self.past_keys)

    def added(self):
        return self.current_keys - self.intersect

    def removed(self):
        return self.past_keys - self.intersect

    def changed(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] == self.current_dict[o])


def convert_back_quantities(value):
    """
    Converts quantities back from dictionary
    """
    result = value
    if isinstance(value, dict):
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
                    result[key] = convert_back_quantities(value)
            except AttributeError:
                pass

    return result


def convert_quantities(value):
    """
    Converts quantities to dictionary
    """
    result = value
    if isinstance(value, dict):
        isnumeric_keys = False
        if (any(isinstance(key, str) for key in value) and
            any(isinstance(key, int) for key in value)):
            raise ValueError('Combination of both "str" and "int" in keys is ' +
                             'not allowed.')
        if all(isinstance(key, int) for key in value):
            isnumeric_keys = True
        elif all(isinstance(key, str) for key in value):
            if all(key.isnumeric() for key in value):
                isnumeric_keys = True
        if isnumeric_keys:
            if not all(int(x) == int(y) + 1
                       for x, y in zip(sorted(value.keys())[1:],
                                       sorted(value.keys()))):
                raise ValueError('Dict keys are numeric, but not monotonously' +
                                 ' increasing by unity when sorted, thus not ' +
                                 'recognized as a list.')
            if not min(int(key) for key in value) != 0:
                raise ValueError('Dict keys are numeric, but not starting ' +
                                 'from 0, thus not recognized as a list.')
    if isinstance(value, pq.Quantity):
        result = {"value": value.magnitude.tolist(),
                  "unit": value.dimensionality.string}
        if isinstance(value, pq.UncertainQuantity):
            assert(value.dimensionality == value.uncertainty.dimensionality)
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


class ActionManager:
    def __init__(self, project):
        self.project = project
        self._db = FirebaseBackend('/actions/' + project.id)

    def __getitem__(self, name):
        result = self._db.get(name)
        if not result:
            raise KeyError("Action '" + name + "' does not exist.")
        return Action(project=self.project, action_id=name)

    def __iter__(self):
        for key in self.keys():
            yield self[key]

    def __contains__(self, name):
        return name in self.keys()

    def keys(self):
        result = self._db.get()
        if result is None:
            result = dict()
        return result.keys()

    def to_dict(self):
        result = self._db.get()
        return result or dict()

    def items(self):
        result = self._db.get()
        if result is None:
            result = dict()
        return result.items()

    def values(self):
        result = self._db.get()
        if result is None:
            result = dict()
        return result.values()


class Project:
    def __init__(self, project_id):
        self.id = project_id
        self._db_actions = FirebaseBackend('/actions/' + project_id)
        self._db_modules = FirebaseBackend('/project_modules/' + project_id)

    @property
    def actions(self):
        return ActionManager(self)

    def require_action(self, name):
        action_data = self._db_actions.get(name)
        if action_data is None:
            dtime = datetime.today().strftime(datetime_format)
            self._db_actions.update(name, {"registered": dtime})
        return Action(self, name)

    def get_action(self, name):
        action_data = self._db_actions.get(name)
        if action_data is None:
            raise NameError('Action "' + name + '" does not exist')
        return Action(self, name)

    def delete_action(self, name):
        action_data = self._db_actions.get(name)
        if action_data is None:
            raise NameError('Action "' + name + '" does not exist.')
        action = Action(self, name)
        for module in action.modules.keys():
            action.delete_module(module)
        action.messages.messages = []
        action.messages.datetimes = []
        action.messages.users = []
        self._db_actions.set(name, {})
        del action

    @property
    def modules(self):
        return ModuleManager(self)

    def require_module(self, name=None, template=None, contents=None,
                       overwrite=False):
        return _require_module(name=name, template=template, contents=contents,
                               overwrite=overwrite, parent=self)

    def get_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise NameError('Module "' + name + '" does not exist')
        return Module(self, name)

    def delete_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise NameError('Module "' + self.id + '" does not exist.')
        self._db_modules.set(name, {})


class FirebaseBackend:
    def __init__(self, path):
        self.path = path

    def exists(self):
        value = self.get()
        if value:
            return True
        else:
            return False

    def get(self, name=None):
        if name is None:
            value = db.child(self.path).get(user["idToken"]).val()
        else:
            value = db.child(self.path).child(name).get(user["idToken"]).val()
        value = convert_back_quantities(value)
        return value

    def set(self, name, value=None):
        if value is None:
            value = name
            value = convert_quantities(value)
            db.child(self.path).set(value, user["idToken"])
        else:
            value = convert_quantities(value)
            db.child(self.path).child(name).set(value, user["idToken"])

    def update(self, name, value=None):
        if value is None:
            value = name
            value = convert_quantities(value)
            db.child(self.path).update(value, user["idToken"])
        else:
            value = convert_quantities(value)
            db.child(self.path).child(name).update(value, user["idToken"])
        value = convert_back_quantities(value)
        return value


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
        else:
            raise IOError('Parent of type "' + type(parent) +
                          '" cannot have modules.')
        self._db = FirebaseBackend(path)

    # TODO module reference id

    def to_dict(self):
        d = self._db.get()
        if d is None:
            return {}
        if '_inherits' in d:
            inherit = FirebaseBackend(d['_inherits']).get()
            inherit.update(d)
            d = inherit
        return d

    def to_json(self, fname=None):
        import json
        fname = fname or self.id
        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError('The filename "' + fname +
                                  '" exists, choose another')
        print('Saving module "' + self.id + '" to "' + fname + '"')
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
                raise ValueError('Got nonempty list, expected dict')
            result = None
        return result


class ModuleManager:
    def __init__(self, parent):
        if isinstance(parent, Action):
            module_path = '/'.join(['action_modules', parent.project.id,
                                    parent.id])
        elif isinstance(parent, Project):
            module_path = '/'.join(['project_modules', parent.id])
        else:
            raise IOError('Parent of type "' + type(parent) +
                          '" cannot have modules.')
        self.parent = parent
        self._db = FirebaseBackend(module_path)

    def __getitem__(self, name):
        return Module(self.parent, name)

    def __iter__(self):
        for name in self.keys():
            yield self[name]

    def __contains__(self, name):
        return name in self.keys()

    def to_dict(self):
        d = {}
        for name in self.keys():
            d[name] = self[name].to_dict()
        return d

    def to_json(self, fname=None):
        import json
        fname = fname or self.parent.id
        if not fname.endswith('.json'):
            fname = fname + '.json'
        if op.exists(fname):
            raise FileExistsError('The filename "' + fname +
                                  '" exists, choose another')
        print('Saving module "' + self.parent.id + '" to "' + fname + '"')
        with open(fname, 'w') as outfile:
            json.dump(self.to_dict(), outfile,
                      sort_keys=True, indent=4)

    def keys(self):
        result = self._get_modules() or {}
        return result.keys()

    def items(self): # TODO does not work with _inherits
        result = self._get_modules() or {}
        return result.items()

    def values(self):
        result = self._get_modules() or {}
        return result.values()

    def _get_modules(self):
        result = self._db.get()
        if isinstance(result, list):
            if len(result) > 0:
                raise TypeError('Got nonempty list, expected dict')
            result = None
        return result


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
    def __init__(self, db_instance, name, dtype=None):
        self._db = db_instance
        self.name = name
        self.dtype = dtype

    @property
    def data(self):
        result = self._db.get(self.name)
        return self.dtype_manager(result, iter_value=True, retrieve=True)

    def __getitem__(self, args):
        data = self.data or []
        return data[args]

    def __iter__(self):
        data = self.data or []
        for d in data:
            yield d

    def __len__(self):
        data = self.data or []
        return len(data)

    def __setitem__(self, args, value):
        data = self.data or []
        result = self.dtype_manager(value)
        data = self.dtype_manager(data, iter_value=True)
        data[args] = result
        self._db.set(self.name, data)

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
        data = self.dtype_manager(data, iter_value=True)
        data.append(result)
        self._db.set(self.name, data)

    def extend(self, value):
        data = self.data or []
        result = self.dtype_manager(value, iter_value=True)
        data = self.dtype_manager(data, iter_value=True)
        data.extend(result)
        self._db.set(self.name, data)

    def dtype_manager(self, value, iter_value=False, retrieve=False):
        if value is None or self.dtype is None:
            return
        if not retrieve:
            if iter_value:
                if not all(isinstance(v, self.dtype) for v in value):
                    raise TypeError('Expected ' + str(self.dtype) + ' got ' +
                                     str([type(v) for v in value]))
            else:
                if not isinstance(value, self.dtype):
                    raise TypeError('Expected ' + str(self.dtype) + ' got ' +
                                 str(type(value)))
        if self.dtype == datetime:
            if iter_value:
                if all(isinstance(v, str) for v in value):
                    return [datetime.strptime(v, datetime_format) for v in value]
                else:
                    return [v.strftime(datetime_format) for v in value]
            else:
                if isinstance(value, str):
                    return datetime.strptime(value, datetime_format)
                else:
                    return value.strftime(datetime_format)
        else:
            return value


class Messages:
    def __init__(self, action):
        path = "/".join(["action_messages", action.project.id, action.id])
        self._db = FirebaseBackend(path)
        self.action = action
        self._messages = ProperyList(self._db, 'messages', dtype=str)
        self._datetimes = ProperyList(self._db, 'datetimes', dtype=datetime)
        self._users = ProperyList(self._db, 'users', dtype=str)

    @property
    def messages(self):
        return [{'message': m, 'datetime': d, 'user': u}
                for m, d, u in zip(self._messages, self._datetimes, self._users)]

    @messages.setter
    def messages(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        self._db.set({})
        for message in value:
            self.append(message)


    def __getitem__(self, arg):
        message = {
            'message': self._messages[arg],
            'user': self._users[arg],
            'datetime': self._datetimes[arg]
        }
        return message

    def __setitem__(self, arg, message):
        if not isinstance(message, dict):
            raise TypeError('Expected "dict", got "' + str(type(message)) + '"')
        if not 'message' in message and 'user' in message and 'datetime' in message:
            raise ValueError('Message must be formated as ' +
                             'dict(message="message", user="user", ' +
                             'datetime="datetime"')
        self._messages[arg] = message['message']
        self._datetimes[arg] = message['datetime']
        self._users[arg] = message['user']

    def append(self, message):
        if not isinstance(message, dict):
            raise TypeError('Expected "dict", got "' + str(type(message)) + '"')
        if not 'message' in message and 'user' in message and 'datetime' in message:
            raise ValueError('Message must be formated as ' +
                             'dict(message="message", user="user", ' +
                             'datetime="datetime"')
        self._messages.append(message['message'])
        self._datetimes.append(message['datetime'])
        self._users.append(message['user'])


class Action:
    def __init__(self, project, action_id):
        self.project = project
        self.id = action_id
        path = "/".join(["actions", self.project.id, self.id])
        self._db = FirebaseBackend(path)
        modules_path = "/".join(["action_modules", self.project.id, self.id])
        self._db_modules = FirebaseBackend(modules_path)

    @property
    def messages(self):
        return Messages(self)

    @messages.setter
    def messages(self, value):
        mes = Messages(self)
        mes.messages = value

    @property
    def location(self):
        return self._db.get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('location', value)

    @property
    def type(self):
        return self._db.get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected "str" got "' + str(type(value)) + '"')
        self._db.set('type', value)

    @property
    def subjects(self):
        return ProperyList(self._db, 'subjects', dtype=str)

    @subjects.setter
    def subjects(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                             str([type(v) for v in value]))
        self._db.set('subjects', value)

    @property
    def datetime(self):
        return datetime.strptime(self._db.get('datetime'), datetime_format)

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, datetime):
            raise TypeError('Expected "datetime" got "' + str(type(value)) +
                            '".')
        dtime = value.strftime(datetime_format)
        self._db.set('datetime', dtime)

    @property
    def users(self):
        return ProperyList(self._db, 'users', dtype=str)

    @users.setter
    def users(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                             str([type(v) for v in value]))
        self._db.set('users', value)

    @property
    def tags(self):
        return ProperyList(self._db, 'tags', dtype=str)

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected "list", got "' + str(type(value)) + '"')
        if not all(isinstance(v, str) for v in value):
            raise TypeError('Expected contents to be "str" got ' +
                             str([type(v) for v in value]))
        self._db.set('tags', value)

    @property
    def modules(self):
        # TODO consider adding support for non-shallow fetching
        return ModuleManager(self)

    def require_module(self, name=None, template=None, contents=None,
                       overwrite=False):
        return _require_module(name=name, template=template, contents=contents,
                               overwrite=overwrite, parent=self)

    def get_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise NameError('Module "' + name + '" does not exist')
        return Module(self, name)

    def delete_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise NameError('Module "' + self.id + '" does not exist.')
        self._db_modules.set(name, {})

    def require_filerecord(self, class_type=None, name=None):
        class_type = class_type or Filerecord
        return class_type(self, name)


def _require_module(name=None, template=None, contents=None,
                    overwrite=False, parent=None):
    assert parent is not None
    if name is None and template is not None:
        template_path = "/".join(["templates", template])
        name = FirebaseBackend(template_path).get('identifier')
        if name is None:
            raise ValueError('Template "' + template + '" has no identifier.')
    if template is None and name is None:
        raise ValueError('name and template cannot both be None.')
    if contents is not None and template is not None:
        raise ValueError('Cannot set contents if a template' +
                         'is requested.')
    if contents is not None:
        if not isinstance(contents, dict):
            raise TypeError('Contents expected "dict", got "' +
                            type(contents) + '".')

    module = Module(parent=parent, module_id=name)
    if module._db.exists():
        if template is not None or contents is not None:
            if not overwrite:
                raise ValueError('Set overwrite to true if you want to ' +
                                 'overwrite the contents of the module.')

    if template is not None:
        template_cont_path = "/".join(["templates_contents", template])
        template_contents = FirebaseBackend(template_cont_path).get()
        # TODO give error if template does not exist
        module._db.set(template_contents)
    if contents is not None:
        if '_inherits' in contents:
            heritage = FirebaseBackend(contents['_inherits']).get()
            if heritage is None:
                raise ValueError(
                    'Can not inherit {}'.format(contents['_inherits']))
            d = DictDiffer(contents, heritage)
            keys = [key for key in list(d.added()) + list(d.changed())]
            diffcont = {key: contents[key] for key in keys}
            module._db.set(diffcont)
        else:
            module._db.set(contents)
    return module


def require_template(template, contents=None, overwrite=False):
    template_db = FirebaseBackend("/templates")
    contents_db = FirebaseBackend("/templates_contents")
    template_contents = contents_db.get()
    result = template_db.get()
    if contents is None and result is None:
        raise ValueError('Template does not exist, please give contents' +
                         'in order to generate a template.')
    elif contents is None and result is not None:
        if template_contents is not None:
            result.update(template_contents)
        return result

    if isinstance(contents, str):
        if op.exists(contents):
            import json
            with open(contents, 'r') as infile:
                contents = json.load(infile)
        else:
            raise FileNotFoundError('File "' + contents + '" not found.')

    if not isinstance(contents, dict):
        raise TypeError('Expected "dict", got "' + type(contents) + '".')
    if not overwrite and template_contents is not None:
        raise ValueError('Set overwrite to true if you want to ' +
                         'overwrite the contents of the template.')
    template_db.set(template, {'identifier': template, 'name': template})
    contents_db.set(template, contents)


def get_template(template):
    template_db = FirebaseBackend("/templates")
    contents_db = FirebaseBackend("/templates_contents")
    template_contents = contents_db.get()
    result = template_db.get()
    if result is None:
        raise NameError('Template "' + template + '" does not exist.')
    name = template_db.get('identifier')
    if name is None:
        raise ValueError('Template "' + template + '" has no identifier.')
    if template_contents is not None:
        result.update(template_contents)
    return result


def delete_template(template):
    template_db = FirebaseBackend("/templates")
    contents_db = FirebaseBackend("/templates_contents")
    template_contents = contents_db.get()
    result = template_db.get()
    if result is None:
        raise NameError('Template "' + template + '" does not exist.')
    contents_db.set({})
    template_db.set({})


def get_project(project_id):
    existing = db.child("/".join(["projects",
                                  project_id])).get(user["idToken"]).val()
    if not existing:
        raise NameError("Project " + project_id + " does not exist.")
    return Project(project_id)


def require_project(project_id):
    """Creates a new project with the provided id."""
    existing = db.child("/".join(["projects",
                                  project_id])).get(user["idToken"]).val()
    registered = datetime.today().strftime(datetime_format)
    if not existing:
        db.child("/".join(["projects",
                           project_id])).set({"registered":
                                              registered}, user["idToken"])
    return Project(project_id)


def delete_project(project_id, remove_all_childs=False):
    """Deletes a project named after the provided id."""
    existing = db.child("/".join(["projects",
                                  project_id])).get(user["idToken"]).val()
    if not existing:
        raise NameError('Project "' + project_id + '" does not exist.')
    else:
        if remove_all_childs:
            project = Project(project_id)
            for action in project.actions.keys():
                project.delete_action(action)
            for module in project.modules.keys():
                project.delete_module(module)
        db.child("/".join(["projects",
                           project_id])).set({}, user["idToken"])


def _init_module():
    """
    Helper function, which can abort if loading fails.
    """
    global db

    config = expipe.settings['firebase']['config']
    firebase = pyrebase.initialize_app(config)
    refresh_token()
    db = firebase.database()

    return True


def refresh_token():
    global auth, user
    config = expipe.settings['firebase']['config']
    firebase = pyrebase.initialize_app(config)
    try:
        email = expipe.settings['firebase']['email']
        password = expipe.settings['firebase']['password']
        auth = firebase.auth()
        user = None
        if email and password:
            user = auth.sign_in_with_email_and_password(email, password)
    except KeyError:
        print("Could not find email and password in configuration.\n"
              "Try running expipe.configure() again.\n"
              "For more info see:\n\n"
              "\texpipe.configure?\n\n")


_init_module()
