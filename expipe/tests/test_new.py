import pytest
from unittest import mock
import expipe



def test_module_get_require_equal_path(create_filesystem_root):
    module_contents = {'species': {'value': 'rat'}}
    backend = expipe.backends.FileSystemBackend('/tmp/' + pytest.MAIN_ID)
    project = expipe.core.require_project(pytest.PROJECT_ID, backend)
    action = project.require_action(pytest.ACTION_ID)

    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)

    project_module2 = project.modules[pytest.MODULE_ID]
    assert project_module._db.path == project_module2._db.path

    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    action_module2 = action.modules[pytest.MODULE_ID]
    assert action_module._db.path == action_module2._db.path
