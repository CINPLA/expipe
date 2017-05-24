import datetime
import exdir
import os
import os.path as op
import uuid
import pyrebase
import configparser
import quantities as pq
import numpy as np
import warnings
from expipe import settings


# TODO add attribute managers to allow changing values of modules and actions

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
            warnings.warn('Keyword "units" is not supported, use "unit" in stead')
        if "unit" in value and "value" in value:
            if isinstance(value['value'], str):
                val = []
                for stuff in value['value'].split(','):
                    if stuff == '':
                        continue
                    try:
                        val.append(float(stuff))
                    except Exception:
                        val.append(stuff)
                        warnings.warn('Could not convert value of type:' +
                                      ' "{}" to float'.format(type(stuff)))
            else:
                val = value['value']
            if "uncertainty" in value:
                try:
                    result = pq.UncertainQuantity(val,
                                                  value["unit"],
                                                  value["uncertainty"])
                except Exception:
                    pass
            else:
                try:
                    result = pq.Quantity(val, value["unit"])
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
    if isinstance(value, pq.Quantity):
        if value.shape in ((), (1, )):  # is scalar
            val = value.magnitude.tolist()
        else:
            val = ', '.join([str(val) for val in value.magnitude.tolist()])
        result = {
            "value": val,
            "unit": value.dimensionality.string
        }
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
        self.datetime_format = '%Y-%m-%dT%H:%M:%S'
        self._db_actions = FirebaseBackend('/actions/' + project_id)
        self._db_modules = FirebaseBackend('/project_modules/' + project_id)

    @property
    def actions(self):
        return ActionManager(self)

    def require_action(self, name):
        result = self._db_actions.get(name)
        if result is None:
            dtime = datetime.datetime.today().strftime(self.datetime_format)
            result = self._db_actions.update(name, {"registered": dtime})
        return Action(self, name)

    def get_action(self, name):
        result = self._db_actions.get(name)
        if result is None:
            raise IOError('Action "' + name + '" does not exist')
        return Action(self, name)

    def delete_action(self, name):
        result = self._db_actions.get(name)
        if result is None:
            raise IOError('Action "' + self.id + '" does not exist.')
        self._db_actions.set(name, {})

    @property
    def modules(self):
        return ModuleManager(self)

    def require_module(self, name):
        result = self._db_modules.get(name)
        return Module(self, name)

    def get_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise IOError('Action "' + name + '" does not exist')
        return Module(self, name)

    def delete_module(self, name):
        result = self._db_modules.get(name)
        if result is None:
            raise IOError('Action "' + self.id + '" does not exist.')
        self._db_modules.set(name, {})


class Datafile:
    def __init__(self, action):
        self.action = action
        action_datafile_directory = op.join(settings["data_path"], action.project)
        os.makedirs(action_datafile_directory, exist_ok=True)
        self.exdir_path = op.join(action_datafile_directory, action.id + ".exdir")
        self.exdir_file = exdir.File(self.exdir_path)
        data = {
            "type": "exdir",
            "exdir_path": self.exdir_path
        }
        dfiles = db.child("datafiles").child(self.action.project.id)
        dfiles.child(self.action.id).child("main").set(data, user["idToken"])


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
            raise ValueError('Module name must be string')
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
            json.dump(module.to_dict(), outfile,
                      sort_keys=True, indent=4)


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

    def keys(self):
        result = self._get_modules()
        if result is None:
            result = dict()
        return result.keys()

    def items(self): # TODO does not work with _inherits
        result = self._get_modules()
        if result is None:
            result = dict()
        return result.items()

    def values(self):
        result = self._get_modules()
        if result is None:
            result = dict()
        return result.values()

    def _get_modules(self):
        result = self._db.get()
        if isinstance(result, list):
            if len(result) > 0:
                raise ValueError('Got nonempty list, expected dict')
            result = None
        return result


class Filerecord:
    def __init__(self, action, filerecord_id=None):
        self.id = filerecord_id or "main"  # oneliner hack by Mikkel
        self.action = action

        # TODO make into properties/functions in case settings change
        self.exdir_path = op.join(action.project.id, action.id,
                                  self.id + ".exdir")
        if 'data_path' in settings:
            self.local_path = op.join(settings["data_path"],
                                      self.exdir_path)
        else:
            self.local_path = None
        if 'server_path' in settings:
            self.server_path = op.join(settings['server']["data_path"],
                                       self.exdir_path)
        else:
            self.server_path = None

        # TODO if not exists and not required, return error
        ref_path = "/".join(["files", action.project.id, action.id])
        self._db = FirebaseBackend(ref_path)
        if not self._db.get(self.id):
            self._db.update(self.id, {"path": self.exdir_path})


class Action:
    def __init__(self, project, action_id):
        self.project = project
        self.id = action_id
        path = "/".join(["actions", self.project.id, self.id])
        self._db = FirebaseBackend(path)

    @property
    def location(self):
        return self._db.get('location')

    @location.setter
    def location(self, value):
        if not isinstance(value, str):
            raise ValueError('Location requires string')
        self._db.set('location', value)

    @property
    def type(self):
        return self._db.get('type')

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise ValueError('Type requires string')
        self._db.set('type', value)

    @property
    def subjects(self):
        return self._db.get('subjects')

    @subjects.setter
    def subjects(self, value):
        if isinstance(value, list):
            value = {val: 'true' for val in value}
        if not isinstance(value, dict):
            raise ValueError('Users requires dict e.g. "{"value": "true"}"')
        else:
            if not all(val == 'true' or val is True for val in value.values()):
                raise ValueError('Users requires a list or a dict formated ' +
                                 'like "{"value": "true"}"')
        self._db.set('subjects', value)

    @property
    def datetime(self):
        return self._db.get('datetime')

    @datetime.setter
    def datetime(self, value):
        if not isinstance(value, datetime.datetime):
            raise ValueError('Datetime requires a datetime object.')
        dtime = value.strftime(self.project.datetime_format)
        self._db.set('datetime', dtime)

    @property
    def users(self):
        return self._db.get('users')

    @users.setter
    def users(self, value):
        if isinstance(value, list):
            value = {val: 'true' for val in value}
        if not isinstance(value, dict):
            raise ValueError('Users requires dict e.g. "{"value": "true"}"')
        else:
            if not all(val == 'true' or val is True for val in value.values()):
                raise ValueError('Users requires a list or a dict formated ' +
                                 'like "{"value": "true"}"')
        self._db.set('users', value)

    @property
    def tags(self):
        return self._db.get('tags')

    @tags.setter
    def tags(self, value):
        if isinstance(value, list):
            value = {val: 'true' for val in value}
        if not isinstance(value, dict):
            raise ValueError('Users requires dict e.g. "{"value": "true"}"')
        else:
            if not all(val == 'true' or val is True for val in value.values()):
                raise ValueError('Users requires a list or a dict formated ' +
                                 'like "{"value": "true"}"')
        self._db.set('tags', value)

    @property
    def modules(self):
        # TODO consider adding support for non-shallow fetching
        return ModuleManager(self)

    def require_module(self, name=None, template=None, contents=None,
                       overwrite=False):
        if name is None and template is not None:
            template_object = db.child("/".join(["templates",
                                                template])).get(
                                                    user["idToken"]).val()
            name = template_object.get('identifier')
            if name is None:
                raise ValueError('Template "' + template + '" has no identifier.')
        if template is None and name is None:
            raise ValueError('name and template cannot both be None.')
        if contents is not None and template is not None:
            raise ValueError('Cannot set contents if a template' +
                             'is required.')
        if contents is not None:
            if not isinstance(contents, dict):
                raise ValueError('Contents must be of type: dict.')

        module = Module(parent=self, module_id=name)
        if module._db.exists():
            if template is not None or contents is not None:
                if not overwrite:
                    raise ValueError('Set overwrite to true if you want to ' +
                                     'overwrite the contents of the module.')
        if template is not None:
            template_contents = db.child("/".join(["templates_contents",
                                                  template])).get(
                                                      user["idToken"]).val()
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

    def require_filerecord(self, class_type=None, name=None):
        class_type = class_type or Filerecord
        return class_type(self, name)


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
    registered = datetime.datetime.today().strftime(datetime_format)
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
        raise IOError('Project "' + project_id + '" does not exist.')
    else:
        if remove_all_childs:
            project = Project(project_id)
            for action in project.actions.keys():
                project.delete_action(action)
            for module in project.modules.keys():
                project.delete_module(module)
        db.child("/".join(["projects",
                           project_id])).set({}, user["idToken"])


def create_datafile(action):
    """
    Creates a new dataset on disk and registers it on the action.
    """
    datafile = Datafile(action)
    datafile.exdir_file.create_group("test")
    return datafile.exdir_file


def find_action(project, user=None, subject=None):
    print("Looking for action by user")
    return None


def _init_module():
    """
    Helper function, which can abort if loading fails.
    """
    global db

    config = settings['firebase']['config']
    firebase = pyrebase.initialize_app(config)
    refresh_token()
    db = firebase.database()

    return True


def refresh_token():
    global auth, user
    config = settings['firebase']['config']
    firebase = pyrebase.initialize_app(config)
    try:
        email = settings['firebase']['email']
        password = settings['firebase']['password']
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

# def create_experiment(session_id, session_start_time, experimenter, session_description="", notes=""):
#     # TODO do we need to require session_id?
#     print(settings)
#
#     unique_id = str(uuid.uuid4())
#     unique_id_short = unique_id.split("-")[0]
#     registration_datetime = datetime.datetime.now()
#     year_folder_name = '{:%Y}'.format(registration_datetime)
#     month_folder_name = '{:%Y-%m}'.format(registration_datetime)
#     exdir_folder_name = '{:%Y-%m-%d-%H%M%S}_{}.exdir'.format(registration_datetime, unique_id_short)
#     parent_path = op.join(settings["data_path"],
#                                year_folder_name,
#                                month_folder_name)
#     if not op.exists(parent_path):
#         os.makedirs(parent_path)
#     exdir_folder_path = op.join(parent_path,
#                                      exdir_folder_name)
#     f = exdir.File(exdir_folder_path)
#     f.attrs["identifier"] = str(unique_id)
#     f.attrs["nwb_version"] = "NWB-1.0.3"
#     f.attrs["file_create_date"] = datetime.datetime.now().isoformat()
#     f.attrs["session_start_time"] = session_start_time
#     f.attrs["session_description"] = session_description
#
#     general = f.create_group("general")
#     general.attrs["session_id"] = session_id
#     general.attrs["experimenter"] = experimenter
#     general.attrs["notes"] = notes
#     # TODO add all /general info from NWB
#
#     f.create_group("acquisition")
#     f.create_group("stimulus")
#     f.create_group("epochs")
#     f.create_group("processing")
#     f.create_group("analysis")
#
#     # TODO add record to database
#
#     # TODO return both ID and file?
#
#     return f
