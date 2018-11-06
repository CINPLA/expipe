import abc

class AbstractBackend(abc.ABC):
    @abc.abstractmethod
    def exists(self, name):
        pass

    @abc.abstractmethod
    def get_project(self, name):
        pass

    @abc.abstractmethod
    def create_project(self, name, contents):
        pass


class AbstractObject(abc.ABC):
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


class AbstractObjectManager(abc.ABC):
    @abc.abstractmethod
    def __getitem__(self, name):
        pass

    @abc.abstractmethod
    def __setitem__(self, name, value):
        pass

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __len__(self):
        pass

    @abc.abstractmethod
    def __contains__(self, name):
        pass


class AbstractListManager(abc.ABC):
    @abc.abstractmethod
    def __getitem__(self, index):
        pass

    @abc.abstractmethod
    def __setitem__(self, index):
        pass

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __len__(self):
        pass

    @abc.abstractmethod
    def __contains__(self, name):
        pass

    @abc.abstractmethod
    def to_list(self):
        pass


class AbstractProject(abc.ABC):
    @property
    @abc.abstractmethod
    def actions(self):
        pass

    @property
    @abc.abstractmethod
    def modules(self):
        pass

    @property
    @abc.abstractmethod
    def attributes(self):
        pass


class AbstractAction(abc.ABC):
    @property
    @abc.abstractmethod
    def messages(self):
        pass

    @property
    @abc.abstractmethod
    def modules(self):
        pass

    @property
    @abc.abstractmethod
    def attributes(self):
        pass

class AbstractEntity(abc.ABC):
    @property
    @abc.abstractmethod
    def modules(self):
        pass

    @property
    @abc.abstractmethod
    def attributes(self):
        pass

class AbstractTemplate(abc.ABC):
    @property
    @abc.abstractmethod
    def contents(self):
        pass

class AbstractModule(abc.ABC):
    @property
    @abc.abstractmethod
    def contents(self):
        pass
