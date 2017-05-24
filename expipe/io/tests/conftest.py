import pytest
import expipe
expipe.ensure_testing()

PROJECT_ID = 'test-project'
ACTION_ID = 'test-action'
MODULE_ID = 'test-module'


def pytest_namespace():
    return {"PROJECT_ID": PROJECT_ID,
            "ACTION_ID": ACTION_ID,
            "MODULE_ID": MODULE_ID}


@pytest.fixture
def teardown_database():
    expipe.delete_project(PROJECT_ID)
