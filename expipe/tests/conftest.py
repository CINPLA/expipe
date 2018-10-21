import pytest
import expipe
import os
import shutil
import pathlib

expipe.ensure_testing()

unique_id = 'test'

MAIN_ID = 'main-' + unique_id
PROJECT_ID = 'project-' + unique_id
ACTION_ID = 'action-' + unique_id
MODULE_ID = 'module-' + unique_id
PROJECT_MODULE_ID = 'project-module-' + unique_id
ACTION_MODULE_ID = 'action-module-' + unique_id


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
    from expipe.backends.filesystem import yaml_dump
    path = pathlib.Path('/tmp') / MAIN_ID
    if path.exists():
        shutil.rmtree(str(path))
    os.makedirs(str(path))

    yaml_dump(path / 'expipe.yaml', {'username': 'Test User'})


@pytest.fixture(scope='function')
def teardown_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
