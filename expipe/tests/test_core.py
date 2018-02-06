import pytest
from unittest import mock
import expipe
from mock_backend import create_mock_backend, db_dummy


db = db_dummy.copy()
db["actions"] = {
    "retina": {
        "ret_1": {
            "type": "recording",
            "location": "room1",
        },
        "ret_2": {
            "type": "surgery",
            "location": "room2",
        },
    },
}


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_action_manager():
    project_id = "retina"
    project = expipe.io.core.Project(project_id)
    action_manager = project.actions

    assert project == action_manager.project
    assert db["actions"]["retina"] == action_manager.to_dict()
    assert db["actions"]["retina"].items() == action_manager.items()
    assert all(k in db["actions"]["retina"].values() for k in action_manager.values())
    assert all(k in db["actions"]["retina"].keys() for k in action_manager.keys())
    assert all(k in action_manager for k in ("ret_1", "ret_2"))

    with pytest.raises(KeyError):
        action_manager["ret_3"]
