import pytest
import expipe
import os
import shutil
import pathlib

unique_id = 'test'

TESTDIR = "/tmp/expipe-tests"
MAIN_ID = 'main-' + unique_id
PROJECT_ID = 'myproject-' + unique_id
PROJECT_MODULE_ID = 'myproject-module-' + unique_id
ACTION_ID = 'myaction-' + unique_id
ACTION_MODULE_ID = 'myaction-module-' + unique_id
ENTITY_ID = 'myentity-' + unique_id
ENTITY_MODULE_ID = 'myentity-module-' + unique_id
TEMPLATE_ID = 'mytemplate-' + unique_id


def pytest_configure():
    pytest.MAIN_ID = MAIN_ID
    pytest.PROJECT_ID = PROJECT_ID
    pytest.PROJECT_MODULE_ID = PROJECT_MODULE_ID
    pytest.ACTION_ID = ACTION_ID
    pytest.ACTION_MODULE_ID = ACTION_MODULE_ID
    pytest.ENTITY_ID = ENTITY_ID
    pytest.ENTITY_MODULE_ID = ENTITY_MODULE_ID
    pytest.TEMPLATE_ID = TEMPLATE_ID


@pytest.fixture(scope='function')
def project_path():
    if os.path.exists(TESTDIR):
        shutil.rmtree(TESTDIR)
    return pathlib.Path(TESTDIR) / PROJECT_ID


@pytest.fixture(scope='function')
def teardown_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
