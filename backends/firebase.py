from ..backend import *
import requests

class FirebaseObjectManager(AbstractObjectManager):
    def __init__(self, path, object_type, backend_type, backend):
        self._db = FirebaseObject(name)
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


class FirebaseBackend(AbstractBackend):
    def __init__(self):
        self.id_token = None
        self.refresh_token = None
        self.token_expiration = dt.datetime.now()

    def project_manager(self):
        return FirebaseObjectManager("projects", Project, FirebaseProject, self)


class FirebaseProject:
    def __init__(self, name):
        self._name = name
        self._attribute_manager = FirebaseObject("/".join("projects", name))
        self._action_manager = FirebaseObjectManager("/".join("actions", name), Action, FirebaseAction, self)

    @property
    def actions(self):
        return self._action_manager

    @property
    def attributes(self):
        return self._attribute_manager


class FirebaseAction:
    def __init__(self, project, name):
        self._attribute_manager = FirebaseObject("/".join("actions", project, name))
        self._message_manager = FirebaseObjectManager("/".join("action_messages", project, name), Message, FirebaseMessage, self)

    def attribute_manager(self):
        return self._attribute_manager

    def message_manager(self):
        return self._message_manager


class FirebaseEntity:
    def __init__(self, project, name):
        self._attribute_manager = FirebaseObject("/".join("entities", project, name))
        self._message_manager = FirebaseObjectManager("/".join("entity_messages", project, name), Message, FirebaseMessage, self)

    def attribute_manager(self):
        return self._attribute_manager

    def message_manager(self):
        return self._message_manager


class FirebaseModule:
    def __init__(self, module_type, project, name=None):
        if module_type == "action":
            assert(name is not None)
            self._content_manager = FirebaseObject("/".join("action_modules", project, name))
        elif module_type == "entity":
            assert(name is not None)
            self._content_manager = FirebaseObject("/".join("entity_modules", project, name))
        elif module_type == "project":
            self._content_manager = FirebaseObject("/".join("project_modules", project))

    def content_manager(self):
        return self._content_manager


class FirebaseTemplate:
    def __init__(self, project, name):
        self._content_manager = FirebaseObject("/".join("projects", project, name))

    def content_manager(self):
        return self._content_manager


class FirebaseObject(AbstractObject):
    def __init__(self, path):
        super(FirebaseObject, self).__init__(
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

    def set(self, name=None, value=None):
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
        self.set(name, {})

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

