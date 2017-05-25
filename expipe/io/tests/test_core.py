import pytest
from datetime import datetime
import expipe
expipe.ensure_testing()


def test_create_delete_project_and_childs(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    expipe.delete_project(pytest.PROJECT_ID, remove_all_childs=True)
    with pytest.raises(NameError):
        expipe.get_project(pytest.PROJECT_ID)
    # remake project, then the "old" action and project_module should be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    with pytest.raises(NameError):
        project.get_action(pytest.ACTION_ID)
        project.get_module(pytest.MODULE_ID)
    # remake action, then the "old" action_module should be deleted
    action = project.require_action(pytest.ACTION_ID)
    with pytest.raises(NameError):
        action.get_module(pytest.MODULE_ID)


def test_create_delete_project_not_childs(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    expipe.delete_project(pytest.PROJECT_ID)
    with pytest.raises(NameError):
        expipe.get_project(pytest.PROJECT_ID)
    # remake project, then the "old" action and action_module should be NOT be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.get_action(pytest.ACTION_ID)
    action.get_module(pytest.MODULE_ID)


def test_create_project(teardown_project):
    expipe.require_project(pytest.PROJECT_ID)


def test_create_action():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.get_action(pytest.ACTION_ID)


def test_create_action_module():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    action.get_module(pytest.MODULE_ID)


def test_create_project_module():
    project = expipe.require_project(pytest.PROJECT_ID)
    module_contents = {'test': {'value': 'youyo'}}
    project.require_module(pytest.MODULE_ID, contents=module_contents)
    project.get_module(pytest.MODULE_ID)
