import pytest
from datetime import datetime
import expipe
expipe.ensure_testing()


def test_add_action():
    print('*****************', expipe.config.settings)
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action.user = 'tester'
    project.get_action(pytest.ACTION_ID)


def test_add_module():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    tracking = action.require_module(pytest.MODULE_ID,
                                     contents={'test': {'value': 'youyo'}})
    project.get_action(pytest.ACTION_ID)
