from ..backend import *
import requests
from ..core import *
import datetime as dt
import expipe
try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml

def deep_verification(default, current, path=""):
    for key in default:
        next_path = key
        if path:
            next_path = path + "." + key

        if key not in current:
            print("WARNING: '{}' not found in settings.".format(next_path),
                  "Please rerun expipe.configure().")
        else:
            if isinstance(default[key], dict):
                if not isinstance(current[key], dict):
                    print("WARNING: Expected '{}' to be dict in settings.".format(next_path),
                          "Please rerun expipe.configure().")
                else:
                    deep_verification(default[key], current[key], path=next_path)


def configure(config_name, data_path, email, password, url_prefix, api_key):
    """
    The configure function creates a configuration file if it does not yet exist.
    Ask your expipe administrator about the correct values for the parameters.

    Parameters
    ----------
    data_path :
        path to where data files should be stored
    email :
        user email on Firebase server
    password :
        user password on Firebase server (WARNING: Will be stored in plain text!)
    url_prefix:
        prefix of Firebase server URL (https://<url_prefix>.firebaseio.com)
    api_key:
        Firebase API key
    """

    config_dir = pathlib.home() / '.config' / 'expipe' / 'firebase'
    config_dir.mkdir(exist_ok=True)
    config_file = (config_dir / config_name).with_suffix(".yaml")

    current_settings = {}
    with open(config_file) as f:
        current_settings = yaml.safe_load(f)

    current_settings.update({
        "data_path": data_path,
        "firebase": {
            "email": email,
            "password": password,
            "config": {
                "apiKey": api_key,
                "authDomain": "{}.firebaseapp.com".format(url_prefix),
                "databaseURL": "https://{}.firebaseio.com".format(url_prefix),
                "storageBucket": "{}.appspot.com".format(url_prefix)
            }
        }
    })

    with open(config_file) as f:
        yaml.dump(current_settings, f, default_flow_style=False)


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


class FirebaseObjectManager(AbstractObjectManager):
    def __init__(self, config, path, path_prefix, object_type, backend_type):
        self.config = config
        self.path = path
        self.path_prefix = path_prefix
        self._db = FirebaseObject(config, path)
        self._object_type = object_type
        self._backend_type = backend_type

    def __getitem__(self, name):
        if not self._db.exists(name):
            raise KeyError("Action '{}' does not exist".format(name))
        if self.path_prefix is not None:
            prefixed_name = "/".join([self.path_prefix, name])
        else:
            prefixed_name = name

        full_path = "/".join([self.path, name])

        return self._object_type(name, self._backend_type(self.config, full_path, prefixed_name))

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


class FirebaseBackend(AbstractBackend):
    def __init__(self, config):
        self.config = config
        self.projects = FirebaseObjectManager(config, "projects", None, Project, FirebaseProject)

    def exists(self, name):
        return name in self.projects

    def get_project(self, name):
        return Project(name, FirebaseProject(self.config, None, name))

    def create_project(self, name, contents):
        self.projects[name] = contents

    def delete_project(self, name, remove_all_children=False):
        raise NotImplementedError("Cannot delete firebase projects")


class FirebaseProject:
    def __init__(self, config, path, name):
        self._attribute_manager = FirebaseObject(config, path)
        self._action_manager = FirebaseObjectManager(
            config,
            "/".join(["actions", name]), name, Action, FirebaseAction)
        self._entities_manager = FirebaseObjectManager(
            config,
            "/".join(["entities", name]), name, Entity, FirebaseEntity)
        self._templates_manager = FirebaseObjectManager(
            config,
            "/".join(["templates", name]), name, Template, FirebaseTemplate)
        self._module_manager = FirebaseObjectManager(
            config,
            "/".join(["project_modules", name]), name, Template, FirebaseTemplate)

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

    @property
    def modules(self):
        return self._module_manager


class FirebaseAction:
    def __init__(self, config, path, name):
        self._attribute_manager = FirebaseObject(config, path)
        self._module_manager = FirebaseObjectManager(
            config,
            "/".join(["action_modules", name]), path, Module, FirebaseModule)
        self._message_manager = FirebaseObjectManager(
            config,
            "/".join(["action_messages", name]), path, Message, FirebaseMessage)

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager


class FirebaseMessage:
    def __init__(self, config, path, name):
        self._content_manager = FirebaseObject(config, path)

    @property
    def contents(self):
        return self._content_manager


class FirebaseEntity:
    def __init__(self, config, path, name):
        self._attribute_manager = FirebaseObject(config, path)
        self._message_manager = FirebaseObjectManager(config, "/".join(["entity_messages", name]), path, Message, FirebaseMessage)
        self._module_manager = FirebaseObjectManager(config, "/".join(["entity_modules", name]), path, Message, FirebaseModule)

    @property
    def modules(self):
        return self._module_manager

    @property
    def attributes(self):
        return self._attribute_manager

    @property
    def messages(self):
        return self._message_manager

class FirebaseModule:
    def __init__(self, config, path, name):
        self._content_manager = FirebaseObject(config, path)

    @property
    def contents(self):
        return self._content_manager


class FirebaseTemplate:
    def __init__(self, config, path):
        self._content_manager = FirebaseObject(config, path)

    def content_manager(self):
        return self._content_manager


class FirebaseObject(AbstractObject):
    def __init__(self, config, path):
        super(FirebaseObject, self).__init__()
        self.id_token = None
        self.refresh_token = None
        self.token_expiration = dt.datetime.now()
        self.path = path
        self.config = config

    def ensure_auth(self):
        current_time = dt.datetime.now()
        api_key = self.config["firebase"]["config"]["apiKey"]

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
            "email": self.config["firebase"]["email"],
            "password": self.config["firebase"]["password"],
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
        database_url = self.config["firebase"]["config"]["databaseURL"]
        result = "{database_url}/{name}.json?auth={id_token}".format(
            database_url=database_url,
            name=full_path,
            id_token=self.id_token
        )
        return result

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
        response = requests.get(url)
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        value = convert_from_firebase(value)
        return value

    # def get_keys(self, name=None):
    #     return self.get(name, shallow=True)

    def set(self, name=None, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        response = requests.put(url, json=value)
        assert(response.status_code == 200)
        value = response.json()
        if value is not None:
            assert("errors" not in value)

    def push(self, name=None, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        response = requests.post(url, json=value)
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        return value

    def delete(self, name):
        self.set(name, {})

    def update(self, name, value=None):
        self.ensure_auth()
        url = self.build_url(name)
        if value is None:
            value = name
        value = convert_to_firebase(value)
        response = requests.patch(url, json=value)
        assert(response.status_code == 200)
        value = response.json()
        if value is None:
            return value
        assert("errors" not in value)
        value = convert_from_firebase(value)
        return value
