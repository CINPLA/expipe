import dpath.util
import yaml
import expipe

db_dummy = {
    "projects": {},
    "project_modules": {},
    "actions": {},
    "action_modules": {},
    "action_messages": {},
    "templates": {},
    "templates_contents": {},
    "files": {}
}


def create_mock_backend(data):

    class MockBackend:
        def __init__(self, path):
            self.path = path
            self.data = data

        def exists(self):
            value = self.path in self.data
            if value:
                return True
            else:
                return False

        def get(self, name=None):
            try:
                if name is None:
                        value = dpath.util.get(glob=self.path, obj=self.data)
                else:
                    if not isinstance(name, str):
                        raise TypeError('Expected "str", not "{}"'.format(type(name)))
                    value = dpath.util.get(glob=self.path + "/" + name, obj=self.data)
            except KeyError:
                value = None
            value = expipe.io.core.convert_from_firebase(value)
            return value

        def get_keys(self, name=None):
            if name is None:
                value = dpath.util.get(glob=self.path, obj=self.data)
            else:
                if not isinstance(name, str):
                    raise TypeError('Expected "str", not "{}"'.format(type(name)))
                value = dpath.util.get(glob=self.path + "/" + name, obj=self.data)
            return value.keys()

        def set(self, name, value=None):
            if value is None:
                value = name
                value = expipe.io.core.convert_to_firebase(value)
                dpath.util.new(path=self.path, obj=self.data, value=value)
            else:
                value = expipe.io.core.convert_to_firebase(value)
                dpath.util.new(path=self.path + "/" + name, obj=self.data, value=value)

        def update(self, name, value=None):
            if value is None:
                value = name
                value = expipe.io.core.convert_to_firebase(value)
                # db.child(self.path).update(value, user["idToken"])
            else:
                value = expipe.io.core.convert_to_firebase(value)
                # db.child(self.path).child(name).update(value, user["idToken"])
            value = expipe.io.core.convert_from_firebase(value)
            return value

    return MockBackend
