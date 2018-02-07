import pytest
from unittest import mock
import expipe
from mock_backend import create_mock_backend, db_dummy

# TODO test to_json
# TODO test filerecord and Datafile and whatever it is for?
# TODO measure coverage
# TODO test if you can give template identifier which is not unique
# TODO support numeric keys without being list
# TODO unique list in action attributes

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


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_module_to_dict():
    from expipe.io.core import DictDiffer
    project_id = "retina"
    action_id = "ret_3"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    project_module = project.require_module(module_name,
                                            contents=module_contents)

    action = project.require_action(action_id)
    action_module = action.require_module(module_name,
                                          contents=module_contents)

    for module_dict in [action_module.to_dict(), project_module.to_dict()]:
        d = DictDiffer(module_dict, module_contents)
        assert d.changed() == set()
        assert d.added() == set()
        assert d.removed() == set()


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_delete_project_and_childs():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)
    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=False)
    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=False)

    expipe.delete_project(project_id, remove_all_childs=True)
    with pytest.raises(NameError):
        expipe.get_project(project_id)

    # remake project, then the "old" action and project_module should be deleted
    project = expipe.require_project(project_id)
    with pytest.raises(NameError):
        project.get_action(action_id)
        project.get_module(module_name)

    # remake action, then the "old" action_module should be deleted
    action = project.require_action(action_id)
    with pytest.raises(NameError):
        # print(action.get_module(module_name))
        action.get_module(module_name)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_delete_project_not_childs():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)

    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=True)

    expipe.delete_project(project_id)
    with pytest.raises(NameError):
        expipe.get_project(project_id)

    # remake project, then the "old" action and action_module should be NOT be deleted
    project = expipe.require_project(project_id)
    action = project.get_action(action_id)
    action.get_module(module_name)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_project():
    project_id = "lgn"
    expipe.require_project(project_id)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_action():
    project_id = "lgn"
    action_id = "lgn_1"

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)
    project.get_action(action_id)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_action_module():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)
    action.get_module(module_name)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_create_project_module():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    project.require_module(module_name, contents=module_contents, overwrite=True)
    project.get_module(module_name)


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_module_get_require_equal_path():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=True)

    project_module2 = project.get_module(module_name)
    assert project_module._db.path == project_module2._db.path

    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)
    action_module2 = action.get_module(module_name)
    assert action_module._db.path == action_module2._db.path


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_delete_action():
    from datetime import datetime, timedelta

    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)
    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)

    mes = action.messages
    time = datetime(2017, 6, 1, 21, 42, 20)
    _datetimes = [time, time - timedelta(minutes=1)]
    _users = ['us1', 'us2']
    _messages = ['mes1', 'mes2']
    mes.messages = [{'message': m, 'user': u, 'datetime': d} for m, u, d in
                    zip(_messages, _users, _datetimes)]

    for attr in ['subjects', 'users', 'tags']:
        setattr(action, attr, ['sub1', 'sub2'])
    assert len(list(action.modules.keys())) != 0
    project.delete_action(action.id)
    with pytest.raises(NameError):
        project.get_action(action_id)

    # remake and assert that all is deleted
    action = project.require_action(action_id)
    assert len(list(action.modules.keys())) == 0
    assert len(list(action_module.keys())) == 0
    for attr in ['subjects', 'users', 'tags']:
        a = getattr(action, attr).data
        assert a is None
    assert len(action.messages.messages) == 0


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_action_attr():
    from datetime import datetime, timedelta
    project_id = "lgn"
    action_id = "lgn_1"

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    for attr in ['subjects', 'users', 'tags']:
        with pytest.raises(TypeError):
            setattr(action, attr, {'dict': 'I am'})
            setattr(action, attr, 'string I am')
    for attr in ['type', 'location']:
        setattr(action, attr, 'string I am')
        with pytest.raises(TypeError):
            setattr(action, attr, {'dict': 'I am'})
            setattr(action, attr, ['list I am'])
    action.datetime = datetime.now()
    with pytest.raises(TypeError):
        action.datetime = 'now I am'


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_action_attr_list():
    project_id = "lgn"
    action_id = "lgn_1"

    project = expipe.io.core.require_project(project_id)
    action = project.require_action(action_id)

    orig_list = ['sub1', 'sub2']
    for attr in ['subjects', 'users', 'tags']:
        prop_list = getattr(action, attr)
        assert isinstance(prop_list, expipe.io.core.ProperyList)
        prop_list.append('sub3')
        orig_list.append('sub3')
        setattr(action, attr, orig_list)
        prop_list = getattr(action, attr)
        prop_list.extend(['sub4'])
        orig_list.extend(['sub4'])
        prop_list = getattr(action, attr)
        assert set(orig_list) == set(prop_list)
        orig_list = ['sub1', 'sub2']


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_module_quantities():
    import quantities as pq
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}

    project = expipe.require_project(project_id)
    action = project.require_action(action_id)
    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_module_array():
    import numpy as np
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"
    quan = np.array([1, 2])
    module_contents = {'quan': quan}

    project = expipe.require_project(project_id)
    action = project.require_action(action_id)
    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


@mock.patch('expipe.io.core.FirebaseBackend', new=create_mock_backend(db))
def test_module_list():
    project_id = "lgn"
    action_id = "lgn_1"
    module_name = "vision"

    project = expipe.require_project(project_id)
    action = project.require_action(action_id)
    list_cont = ['list I am', 1]
    project_module = project.require_module(module_name,
                                            contents=list_cont,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict, list)
    assert all(a == b for a, b in zip(list_cont, mod_dict))

    module_contents = {'list': list_cont}
    project_module = project.require_module(module_name,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_dict['list']))

    module_contents = {'is_list': {'0': 'df', '1': 'd', '2': 's'}}
    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)

    module_contents = {'almost_list1': {'0': 'df', '1': 'd', 'd': 's'}}
    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['almost_list1'], dict)
    diff = expipe.io.core.DictDiffer(module_contents, mod_dict)
    assert diff.changed() == set(), '{}, {}'.format(module_contents, mod_dict)

    module_contents = {'almost_list2': {'0': 'df', '1': 'd', '5': 's'}}
    with pytest.raises(ValueError):
        action_module = action.require_module(module_name,
                                              contents=module_contents,
                                              overwrite=True)

    module_contents = {'not_list': {'0': 'df', '1': 'd', 5: 's'}}
    with pytest.raises(TypeError):
        action_module = action.require_module(module_name,
                                              contents=module_contents,
                                              overwrite=True)

    module_contents = {'not_list': {'1': 'df', '2': 'd', '3': 's'}}
    with pytest.raises(ValueError):
        action_module = action.require_module(module_name,
                                              contents=module_contents,
                                              overwrite=True)

    module_contents = {'not_list': {0: 'df', 1: 'd', 5: 's'}}
    with pytest.raises(ValueError):
        action_module = action.require_module(module_name,
                                              contents=module_contents,
                                              overwrite=True)

    module_contents = {'is_list': {0: 'df', 1: 'd', 2: 's'}}
    action_module = action.require_module(module_name,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)
