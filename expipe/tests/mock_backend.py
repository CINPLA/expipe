import dpath.util
import expipe


def create_mock_backend(data=None):
    data = {} if data is None else data

    class MockBackend:
        def __init__(self, path):
            self.path = path
            self.data = data

        def exists(self, name=None):
            value = self.get(name)
            if value is not None:
                return True
            else:
                return False

        def get(self, name=None, shallow=False):
            try:
                if name is None:
                    value = dpath.util.get(glob=self.path, obj=self.data)
                else:
                    if not isinstance(name, str):
                        raise TypeError('Expected "str", not "{}"'.format(type(name)))
                    value = dpath.util.get(glob=self.path + "/" + name, obj=self.data)
            except KeyError:
                value = None
            value = expipe.core.convert_from_firebase(value)
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
                value = expipe.core.convert_to_firebase(value)
                dpath.util.new(path=self.path, obj=self.data, value=value)
            else:
                value = expipe.core.convert_to_firebase(value)
                dpath.util.new(path=self.path + "/" + str(name), obj=self.data, value=value)

        def delete(self, name):
            dpath.util.delete(glob=self.path + "/" + str(name), obj=self.data)

        def update(self, name, value=None):
            if value is None:
                value = name
                value = expipe.core.convert_to_firebase(value)
                dpath.util.new(path=self.path, obj=self.data, value=value)
                # db.child(self.path).update(value, user["idToken"])
            else:
                value = expipe.core.convert_to_firebase(value)
                dpath.util.new(path=self.path + "/" + name, obj=self.data, value=value)
                # db.child(self.path).child(name).update(value, user["idToken"])
            value = expipe.core.convert_from_firebase(value)
            return value

    return MockBackend
