import pytest
from unittest import mock
import expipe
from mock_backend import create_mock_backend, db_dummy


db = db_dummy.copy()
db["projects"] = {
    "retina": 1,
    "lgn": 2
}
db["actions"] = {
    "retina": {
        "ret_1": {},
        "ret_2": {},
    },
    "lgn": {
        "lgn_1": {},
        "lgn_2": {},
    }
}


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_action_manager():
    project_id = "retina"
    project = expipe.io.core.Project(project_id)
    action_manager = project.actions

    print("keys", action_manager.keys())
    print("to_dict", action_manager.to_dict())
    print("items", action_manager.items())
    print("values", action_manager.values())
