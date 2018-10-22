import pytest
import expipe
import os
import shutil
import pathlib

expipe.ensure_testing()

unique_id = 'test'

MAIN_ID = 'main-' + unique_id
PROJECT_ID = 'myproject-' + unique_id
ACTION_ID = 'myaction-' + unique_id
MODULE_ID = 'mymodule-' + unique_id
PROJECT_MODULE_ID = 'myproject-module-' + unique_id
ACTION_MODULE_ID = 'myaction-module-' + unique_id


def pytest_namespace():
    return {
        'MAIN_ID': MAIN_ID,
        "PROJECT_ID": PROJECT_ID,
        "ACTION_ID": ACTION_ID,
        "MODULE_ID": MODULE_ID,
        "PROJECT_MODULE_ID": PROJECT_MODULE_ID,
        "ACTION_MODULE_ID": ACTION_MODULE_ID
    }

def pytest_addoption(parser):
    parser.addoption("--firebase", action="store_true", default=False)

@pytest.fixture(scope='function')
def create_url(request):
    if request.config.getoption("--firebase"):
        raise NotImplementedError("Firebase test not implemented")

    path = pathlib.Path('/tmp') / MAIN_ID
    if path.exists():
        shutil.rmtree(str(path))
    os.makedirs(str(path))
    return path / PROJECT_ID


@pytest.fixture(scope='function')
def teardown_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
