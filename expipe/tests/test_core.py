import pytest
from unittest import mock
import expipe
from mock_backend import create_mock_backend

# TODO test to_json
# TODO test filerecord and Datafile and whatever it is for?
# TODO measure coverage
# TODO test if you can give template identifier which is not unique
# TODO support numeric keys without being list
# TODO unique list in action attributes


db = {
    "actions": {
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
}


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend(db))
def test_action_manager():
    PROJECT_ID = "retina"
    project = expipe.core.Project(PROJECT_ID)
    action_manager = project.actions

    assert project == action_manager.project
    assert db["actions"]["retina"] == action_manager.to_dict()
    assert db["actions"]["retina"].items() == action_manager.items()
    assert all(k in db["actions"]["retina"].values() for k in action_manager.values())
    assert all(k in db["actions"]["retina"].keys() for k in action_manager.keys())
    assert all(k in action_manager for k in ("ret_1", "ret_2"))

    with pytest.raises(KeyError):
        action_manager["ret_3"]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_to_dict():
    from expipe.core import DictDiffer

    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)

    for module_dict in [action_module.to_dict(), project_module.to_dict()]:
        d = DictDiffer(module_dict, module_contents)
        assert d.changed() == set()
        assert d.added() == set()
        assert d.removed() == set()


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_delete_project_and_childs():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=False)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=False)

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
        # print(action.get_module(pytest.MODULE_ID))
        action.get_module(pytest.MODULE_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_delete_project_not_childs():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)

    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)

    expipe.delete_project(pytest.PROJECT_ID)
    with pytest.raises(NameError):
        expipe.get_project(pytest.PROJECT_ID)

    # remake project, then the "old" action and action_module should be NOT be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.get_action(pytest.ACTION_ID)
    action.get_module(pytest.MODULE_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_project():

    expipe.require_project(pytest.PROJECT_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_action():
    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.get_action(pytest.ACTION_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_action_module():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)
    action.get_module(pytest.MODULE_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_project_module():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project.require_module(pytest.MODULE_ID, contents=module_contents, overwrite=True)
    project.get_module(pytest.MODULE_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_get_require_equal_path():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)

    project_module2 = project.get_module(pytest.MODULE_ID)
    assert project_module._db.path == project_module2._db.path

    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)
    action_module2 = action.get_module(pytest.MODULE_ID)
    assert action_module._db.path == action_module2._db.path


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_delete_action():
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(pytest.MODULE_ID,
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
        project.get_action(pytest.ACTION_ID)

    # remake and assert that all is deleted
    action = project.require_action(pytest.ACTION_ID)
    assert len(list(action.modules.keys())) == 0
    assert len(list(action_module.keys())) == 0
    for attr in ['subjects', 'users', 'tags']:
        a = getattr(action, attr).data
        assert a is None
    assert len(action.messages.messages) == 0


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_attr():
    from datetime import datetime, timedelta
    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

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


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_attr_list():
    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    orig_list = ['sub1', 'sub2']
    for attr in ['subjects', 'users', 'tags']:
        prop_list = getattr(action, attr)
        assert isinstance(prop_list, expipe.core.ProperyList)
        prop_list.append('sub3')
        orig_list.append('sub3')
        setattr(action, attr, orig_list)
        prop_list = getattr(action, attr)
        prop_list.extend(['sub4'])
        orig_list.extend(['sub4'])
        prop_list = getattr(action, attr)
        assert set(orig_list) == set(prop_list)
        orig_list = ['sub1', 'sub2']


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_quantities():
    import quantities as pq
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}

    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_array():
    import numpy as np
    quan = np.array([1, 2])
    module_contents = {'quan': quan}

    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_attr_list_dtype():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    for attr in ['subjects', 'users', 'tags']:
        with pytest.raises(TypeError):
            setattr(action, attr, ['sub1', 'sub2', 1])
        with pytest.raises(TypeError):
            setattr(action, attr, ['sub1', 'sub2', ['s']])
        setattr(action, attr, ['sub1', 'sub2'])
        prop_list = getattr(action, attr)
        with pytest.raises(TypeError):
            prop_list.append(1)
        with pytest.raises(TypeError):
            prop_list.extend([1])


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_messages_append():
    from datetime import datetime, timedelta
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    time = datetime(2017, 6, 1, 21, 42, 20)
    mes = action.messages
    _messages = ['sub3']
    _datetimes = [time + timedelta(minutes=10)]
    _users = ['usr3']

    message = {'message': 'sub3', 'user': 'usr3',
               'datetime': time + timedelta(minutes=10)}
    mes.messages.append(message)
    messages = [message]

    assert all([expipe.core.DictDiffer(m1, m2).changed() == set()
                for m1, m2 in zip(messages, mes.messages)])


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_messages_dtype():
    from datetime import datetime, timedelta
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    mes = action.messages
    time = datetime(2017, 6, 1, 21, 42, 20)

    # string in date not ok
    _messages = ['mes1', 'mes']
    _datetimes = [time, 'time - timedelta(minutes=1)']
    _users = ['us1', 'None']
    messages = [{'message': m, 'datetime': d, 'user': u}
                for m, d, u in zip(_messages, _datetimes, _users)]
    with pytest.raises(TypeError):
        action.messages = messages

    # int not ok
    _messages = ['mes1', 'mes']
    _datetimes = [time, time - timedelta(minutes=1)]
    _users = ['us1', 1]
    messages = [{'message': m, 'datetime': d, 'user': u}
                for m, d, u in zip(_messages, _datetimes, _users)]
    with pytest.raises(TypeError):
        action.messages = messages

    # int not ok
    _messages = ['mes1', 1]
    _datetimes = [time, time - timedelta(minutes=1)]
    _users = ['us1', 'None']
    messages = [{'message': m, 'datetime': d, 'user': u}
                for m, d, u in zip(_messages, _datetimes, _users)]
    with pytest.raises(TypeError):
        action.messages = messages

    # None is not ok
    _messages = ['mes1', 'mes']
    _datetimes = [time, time - timedelta(minutes=1)]
    _users = ['us1', None]
    messages = [{'message': m, 'datetime': d, 'user': u}
                for m, d, u in zip(_messages, _datetimes, _users)]
    with pytest.raises(TypeError):
        action.messages = messages


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_list():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=list_cont,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict, list)
    assert all(a == b for a, b in zip(list_cont, mod_dict))

    module_contents = {'list': list_cont}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_dict['list']))

    module_contents = {'is_list': {'0': 'df', '1': 'd', '2': 's'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)

    module_contents = {'almost_list1': {'0': 'df', '1': 'd', 'd': 's'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['almost_list1'], dict)
    diff = expipe.core.DictDiffer(module_contents, mod_dict)
    assert diff.changed() == set(), '{}, {}'.format(module_contents, mod_dict)

    module_contents = {'is_list': {0: 'df', 1: 'd', 2: 's'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents,
                                          overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)


# @mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
# def test_action_messages_setter():
#     from datetime import datetime, timedelta
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     time = datetime(2017, 6, 1, 21, 42, 20)
#
#     _messages = ['mes1', 'mes2']
#     _datetimes = [time, time - timedelta(minutes=1)]
#     _users = ['us1', 'us2']
#
#     messages = [{'message': m, 'datetime': d, 'user': u}
#                 for m, d, u in zip(_messages, _datetimes, _users)]
#     action.messages = messages
#     mes = action.messages
#     assert all([expipe.core.DictDiffer(m1, m2).changed() == set()
#                 for m1, m2 in zip(messages, mes.messages)]), '{}, {}'.format(messages, mes.messages)
#
#     new_message = {'message': 'sub3', 'user': 'usr3',
#                    'datetime': time + timedelta(minutes=10)}
#     mes[1] = new_message
#     messages[1] = new_message
#     print(mes.messages)
#     assert all([expipe.core.DictDiffer(m1, m2).changed() == set()
#                 for m1, m2 in zip(messages, mes.messages)])
#     assert expipe.core.DictDiffer(messages[1], mes.messages[1]).changed() == set()

# @mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
# def test_fill_the_project():
#     import quantities as pq
#     from datetime import datetime, timedelta

#     module_contents = {'species': {'value': 'rat'}}
#
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#
#     quan = [1, 2] * pq.s
#     module_contents = {'quan': quan}
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents,
#                                             overwrite=True)
#     mod_dict = project_module.to_dict()
#     assert isinstance(mod_dict['quan'], pq.Quantity)
#     assert all(a == b for a, b in zip(quan, mod_dict['quan']))
#
#     time = datetime(2017, 6, 1, 21, 42, 20)
#
#     _messages = ['mes1', 'mes2']
#     _datetimes = [time, time - timedelta(minutes=1)]
#     _users = ['us1', 'us2']
#
#     messages = [{'message': m, 'datetime': d, 'user': u}
#                 for m, d, u in zip(_messages, _datetimes, _users)]
#     action.messages = messages
#     mes = action.messages
#
#     orig_list = ['sub1', 'sub2']
#     for attr in ['subjects', 'users', 'tags']:
#         prop_list = getattr(action, attr)
#         assert isinstance(prop_list, expipe.core.ProperyList)
#         prop_list.append('sub3')
#         orig_list.append('sub3')
#         setattr(action, attr, orig_list)
#         prop_list.extend(['sub3'])
#         orig_list.extend(['sub3'])
#         prop_list[1] = 'subsub'
#         orig_list[1] = 'subsub'
