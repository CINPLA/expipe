import pytest
from unittest import mock
import expipe
import datetime as dt
import pathlib

def test_create(create_url):
    module_contents = {'species': {'value': 'rat'}}
    project = expipe.core.require_project(create_url)
    assert isinstance(project, expipe.core.Project)
    print('test', project._backend.path)
    action = project.require_action(pytest.ACTION_ID)

    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)

    project_module2 = project.modules[pytest.PROJECT_MODULE_ID]
    assert project_module._backend.path == project_module2._backend.path
    assert project_module.to_dict() == project_module2.to_dict()

    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    action_module2 = action.modules[pytest.ACTION_MODULE_ID]
    assert action_module._backend.path == action_module2._backend.path
    assert action_module.to_dict() == action_module2.to_dict()

    action.create_message("blah", "blah")
    with pytest.raises(KeyError):
        action.create_message("blah", "blah")

    for message in action.messages:
        print(message)
