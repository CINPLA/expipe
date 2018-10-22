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


@pytest.fixture(scope='function')
def create_filesystem_root():
    path = pathlib.Path('/tmp') / MAIN_ID
    if path.exists():
        shutil.rmtree(str(path))
    os.makedirs(str(path))


@pytest.fixture(scope='function')
def teardown_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
