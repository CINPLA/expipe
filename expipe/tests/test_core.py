import pytest
from unittest import mock
import expipe
from mock_backend import create_mock_backend

# TODO test _assert_message_dtype
# TODO test entities
# TODO test _load_template
# TODO test _create_module
# TODO test filerecord and Datafile and whatever it is for?
# TODO test if you can give template identifier which is not unique
# TODO support numeric keys without being list
# TODO unique list in action attributes

######################################################################################################
# Action and ActionManager
######################################################################################################
db_action_manager = {
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


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend(db_action_manager))
def test_action_manager():
    PROJECT_ID = "retina"
    project = expipe.core.Project(PROJECT_ID)
    action_manager = project.actions

    assert project == action_manager.project
    assert db_action_manager["actions"]["retina"] == action_manager.to_dict()
    assert set(list(db_action_manager["actions"]["retina"].keys())) == set(list(action_manager.keys()))
    assert all(k in action_manager for k in ("ret_1", "ret_2"))

    with pytest.raises(KeyError):
        action_manager["ret_3"]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_attr():
    from datetime import datetime, timedelta
    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    for attr in ['entities', 'users', 'tags']:
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
    for attr in ['entities', 'users', 'tags']:
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
def test_action_attr_list_dtype():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    for attr in ['entities', 'users', 'tags']:
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


######################################################################################################
# Module and ModuleManager
######################################################################################################
db_module_manager = {
    "project_modules": {
        "retina": {
            "ret_1": [0, 1, 2],
            "ret_2": {
                "type": "surgery",
                "location": "room2",
            },
        },
    }
}


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend(db_module_manager))
def test_module_manager():
    PROJECT_ID = "retina"
    project = expipe.core.Project(PROJECT_ID)
    module_manager = project.modules
    module = db_module_manager["project_modules"]["retina"]

    assert project == module_manager.parent
    assert module == module_manager.to_dict()
    assert all(k in module_manager for k in ("ret_1", "ret_2"))
    assert set(list(module.keys())) == set(list(module_manager.keys()))

    with pytest.raises(KeyError):
        module_manager["ret_3"]

    with pytest.raises(TypeError):
        expipe.core.ModuleManager(parent=None)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_to_dict():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents)

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents)

    for module_dict in [action_module.to_dict(), project_module.to_dict()]:
        assert module_dict == module_contents


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_quantities():
    import quantities as pq
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}

    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.create_module(pytest.MODULE_ID,
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
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_get_require_equal_path():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
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


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_module_list():
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=list_cont,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict, list)
    assert all(a == b for a, b in zip(list_cont, mod_dict))

    module_contents = {'list': list_cont}
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_dict['list']))

    module_contents = {'is_list': {'0': 'df', '1': 'd', '2': 's'}}
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)

    module_contents = {'almost_list1': {'0': 'df', '1': 'd', 'd': 's'}}
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['almost_list1'], dict)
    assert module_contents == mod_dict, '{}, {}'.format(module_contents, mod_dict)

    module_contents = {'is_list': {0: 'df', 1: 'd', 2: 's'}}
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)


######################################################################################################
# Message and MessageManager
######################################################################################################
def contain_same(A, B):
    cont = []
    if len(A) != len(B):
        return False
    for a in A:
        cont.append(a in B)
    return sum(cont) == len(A)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_messages_setter():
    from datetime import datetime, timedelta
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages

    assert len(message_manager) == 0

    time = datetime(2017, 6, 1, 21, 42, 20)
    text = "my message"
    user = "user1"

    msg_1 = {'text': text, 'user': user, 'datetime': time}

    messages = [msg_1]
    msg_object = action.create_message(text=text, user=user, datetime=time)

    assert isinstance(msg_object, expipe.core.Message)
    assert msg_object.text == text
    assert msg_object.user == user
    assert msg_object.datetime == time

    assert contain_same(messages, message_manager)

    text = "my new message"
    user = "user2"
    msg_2 = {'text': text, 'user': user, 'datetime': time}
    messages.append(msg_2)
    msg_object = action.create_message(text=text, user=user, datetime=time)

    assert isinstance(msg_object, expipe.core.Message)
    assert msg_object.text == text
    assert msg_object.user == user
    assert msg_object.datetime == time

    assert contain_same(messages, message_manager)

    text = "updated text"
    user = "new user"
    time = datetime(2019, 6, 1, 21, 42, 20)

    msg_object.text = text
    msg_object.user = user
    msg_object.datetime = time

    assert msg_object.text == text
    assert msg_object.user == user
    assert msg_object.datetime == time


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_action_messages_dtype():
    from datetime import datetime, timedelta
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    time = datetime(2017, 6, 1, 21, 42, 20)

    # string in date not ok
    msg = {'message': 'sub2', 'user': 'usr2',
           'datetime': str(time + timedelta(minutes=10))}

    with pytest.raises(TypeError):
        action.create_message(msg)

    # int not ok
    msg = {'message': 'sub2', 'user': 13,
           'datetime': time + timedelta(minutes=10)}
    with pytest.raises(TypeError):
        action.create_message(msg)

    # int not ok
    msg = {'message': 12, 'user': "usr2",
           'datetime': time + timedelta(minutes=10)}

    with pytest.raises(TypeError):
        action.create_message(msg)

    # None is not ok
    msg = {'message': "sub2", 'user': None,
           'datetime': time + timedelta(minutes=10)}

    with pytest.raises(TypeError):
        action.create_message(msg)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_change_message():
    from datetime import datetime, timedelta
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages
    time = datetime(2017, 6, 1, 21, 42, 20)

    # add two messages
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    action.create_message(text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    # assert all([m1 == m2.to_dict() for m1, m2 in zip([msg_1, msg_2], message_manager)])

    # change one of them
    msg_3 = {'text': 'sub3', 'user': 'usr3',
             'datetime': time + timedelta(minutes=20)}

    for i, message in enumerate(message_manager):
        if message.user == "usr2":
            message.text = msg_3["text"]
            message.user = msg_3["user"]
            message.datetime = msg_3["datetime"]

    assert contain_same([msg_1, msg_3], message_manager)


######################################################################################################
# create/delete
######################################################################################################
@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_delete_project_and_childs():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=False)
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=False)

    expipe.delete_project(pytest.PROJECT_ID, remove_all_childs=True)
    with pytest.raises(KeyError):
        expipe.get_project(pytest.PROJECT_ID)

    # remake project, then the "old" action and project_module should be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    with pytest.raises(KeyError):
        project.actions[pytest.ACTION_ID]
        project.modules[pytest.MODULE_ID]

    # remake action, then the "old" action_module should be deleted
    action = project.require_action(pytest.ACTION_ID)
    with pytest.raises(KeyError):
        action.modules[pytest.MODULE_ID]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_delete_project_not_childs():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)

    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)

    expipe.delete_project(pytest.PROJECT_ID)
    with pytest.raises(KeyError):
        expipe.get_project(pytest.PROJECT_ID)

    # remake project, then the "old" action and action_module should be NOT be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.actions[pytest.ACTION_ID]
    action.modules[pytest.MODULE_ID]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_project():
    expipe.require_project(pytest.PROJECT_ID)


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_action():
    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.actions[pytest.ACTION_ID]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_action_module():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    action.modules[pytest.MODULE_ID]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_create_project_module():
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project.create_module(pytest.MODULE_ID, contents=module_contents, overwrite=True)
    project.modules[pytest.MODULE_ID]


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_delete_action():
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.core.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages
    action_module = action.create_module(pytest.MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)

    time = datetime(2017, 6, 1, 21, 42, 20)
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    action.create_message(text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    for attr in ['entities', 'users', 'tags']:
        setattr(action, attr, ['sub1', 'sub2'])
    assert len(list(action.modules.keys())) != 0
    project.delete_action(action.id)
    with pytest.raises(KeyError):
        project.actions[pytest.ACTION_ID]

    # remake and assert that all is deleted
    action = project.require_action(pytest.ACTION_ID)
    assert len(list(action.modules.keys())) == 0
    assert len(list(action_module.keys())) == 0
    for attr in ['entities', 'users', 'tags']:
        a = getattr(action, attr).data
        assert a is None
    assert len(action.messages) == 0


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_require_create_get_action():
    project = expipe.core.require_project(pytest.PROJECT_ID)

    # Get a non-existing action
    with pytest.raises(KeyError):
        action = project.actions[pytest.ACTION_ID]

    # Create an existing action
    action = project.create_action(pytest.ACTION_ID)
    with pytest.raises(NameError):
        action = project.create_action(pytest.ACTION_ID)

    # Require an existing action
    action_req = project.require_action(pytest.ACTION_ID)
    assert action_req.id == action.id

    # delete action
    project.delete_action(pytest.ACTION_ID)
    with pytest.raises(KeyError):
        action = project.actions[pytest.ACTION_ID]

    # Require a non-existing action
    action_req = project.require_action(pytest.ACTION_ID)
    action = project.actions[pytest.ACTION_ID]
    assert action_req.id == action.id


@mock.patch('expipe.core.FirebaseBackend', new=create_mock_backend())
def test_fill_the_project():
    import quantities as pq
    from datetime import datetime, timedelta

    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}
    project_module = project.create_module(pytest.MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))

    # time = datetime(2017, 6, 1, 21, 42, 20)
    # msg_1 = {'message': 'sub1', 'user': 'usr1',
    #          'datetime': time}
    #
    # msg_2 = {'message': 'sub2', 'user': 'usr2',
    #          'datetime': time + timedelta(minutes=10)}
    #
    # action.create_message(msg_1)
    # action.create_message(msg_2)

    # orig_list = ['sub1', 'sub2']
    # for attr in ['entities', 'users', 'tags']:
    #     prop_list = getattr(action, attr)
    #     assert isinstance(prop_list, expipe.core.ProperyList)
    #     prop_list.append('sub3')
    #     orig_list.append('sub3')
    #     setattr(action, attr, orig_list)
    #     prop_list.extend(['sub3'])
    #     orig_list.extend(['sub3'])
    #     prop_list[1] = 'subsub'
    #     orig_list[1] = 'subsub'
