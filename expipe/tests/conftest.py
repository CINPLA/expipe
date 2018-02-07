import pytest
import expipe
from expipe.core import DictDiffer

expipe.ensure_testing()

unique_id = 'test'

PROJECT_ID = 'project-' + unique_id
ACTION_ID = 'action-' + unique_id
MODULE_ID = 'module-' + unique_id


def pytest_namespace():
    return {"PROJECT_ID": PROJECT_ID,
            "ACTION_ID": ACTION_ID,
            "MODULE_ID": MODULE_ID}


@pytest.fixture(scope='function')
def setup_dict():
    a = {'a': 1, 'b': 1, 'c': 0}
    b = {'a': 1, 'b': 2, 'd': 0}
    yield DictDiffer(b, a)


@pytest.fixture(scope='function')
def teardown_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
