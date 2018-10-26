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


def test_action_attr(load_database):
    from datetime import datetime, timedelta
    project = load_database.require_project(pytest.PROJECT_ID)
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


def test_action_attr_list(load_database):
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    orig_list = ['sub1', 'sub2']
    for attr in ['entities', 'users', 'tags']:
        prop_list = getattr(action, attr)
        assert isinstance(prop_list, expipe.core.PropertyList)
        prop_list.append('sub3')
        orig_list.append('sub3')
        setattr(action, attr, orig_list)
        prop_list = getattr(action, attr)
        prop_list.extend(['sub4'])
        orig_list.extend(['sub4'])
        prop_list = getattr(action, attr)
        assert set(orig_list) == set(prop_list)
        orig_list = ['sub1', 'sub2']


def test_action_attr_list_dtype(load_database):
    project = load_database.require_project(pytest.PROJECT_ID)
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


# def test_module_manager(load_database):
    # pytest.PROJECT_ID = "retina"
    # project = expipe.core.Project(pytest.PROJECT_ID)
    # module_manager = project.modules
    # module = db_module_manager["project_modules"]["retina"]

    # assert project == module_manager.parent
    # assert module == module_manager.to_dict()
    # assert all(k in module_manager for k in ("ret_1", "ret_2"))
    # assert set(list(module.keys())) == set(list(module_manager.keys()))

    # with pytest.raises(KeyError):
        # module_manager["ret_3"]

    # with pytest.raises(TypeError):
        # expipe.core.ModuleManager(parent=None)


def test_module_to_dict(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents)

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents)

    for module_dict in [action_module.to_dict(), project_module.to_dict()]:
        assert module_dict == module_contents


def test_module_quantities(load_database):
    import quantities as pq
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


def test_module_array(load_database):
    import numpy as np
    quan = np.array([1, 2])
    module_contents = {'quan': quan}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


def test_module_get_require_equal_path(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)

    project_module2 = project.modules[pytest.PROJECT_MODULE_ID]
    assert project_module._backend.path == project_module2._backend.path

    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    action_module2 = action.modules[pytest.ACTION_MODULE_ID]
    assert action_module._backend.path == action_module2._backend.path


def test_module_list(load_database):
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=list_cont,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict, list)
    assert all(a == b for a, b in zip(list_cont, mod_dict))

    module_contents = {'list': list_cont}
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_dict['list']))

    module_contents = {'is_list': {'0': 'df', '1': 'd', '2': 's'}}
    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)

    module_contents = {'almost_list1': {'0': 'df', '1': 'd', 'd': 's'}}
    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['almost_list1'], dict)
    assert module_contents == mod_dict, '{}, {}'.format(module_contents, mod_dict)

    module_contents = {'is_list': {0: 'df', 1: 'd', 2: 's'}}
    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], dict)


######################################################################################################
# Message and MessageManager
######################################################################################################

# TODO should check that we get a dict that contains the same items
def test_action_messages_setter(load_database):
    from datetime import datetime, timedelta
    project = load_database.require_project(pytest.PROJECT_ID)
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

    time = datetime(2017, 6, 1, 21, 42, 21)
    text = "my new message"
    user = "user2"
    msg_2 = {'text': text, 'user': user, 'datetime': time}
    messages.append(msg_2)
    msg_object = action.create_message(text=text, user=user, datetime=time)

    assert isinstance(msg_object, expipe.core.Message)
    assert msg_object.text == text
    assert msg_object.user == user
    assert msg_object.datetime == time

    text = "updated text"
    user = "new user"
    time = datetime(2019, 6, 1, 21, 42, 22)

    msg_object.text = text
    msg_object.user = user
    msg_object.datetime = time

    assert msg_object.text == text
    assert msg_object.user == user
    assert msg_object.datetime == time


def test_action_messages_dtype(load_database):
    from datetime import datetime, timedelta
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    time = datetime(2017, 6, 1, 21, 42, 23)

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


def test_change_message(load_database):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages
    time = datetime(2017, 6, 1, 21, 42, 20)

    # add two messages
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    messages = {
        datetime.strftime(time, format): msg_1,
        datetime.strftime(time + timedelta(minutes=10), format): msg_2
    }
    action.create_message(
        text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(
        text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    for message_id, message in message_manager.items():
        assert messages[message_id] == message.to_dict()

    # change one of them
    msg_3 = {'text': 'sub3', 'user': 'usr3',
             'datetime': time + timedelta(minutes=20)}

    messages[datetime.strftime(time + timedelta(minutes=10), format)] = msg_3
    for message_id in message_manager:
        message = message_manager[message_id]
        if message.user == "usr2":
            message.text = msg_3["text"]
            message.user = msg_3["user"]
            message.datetime = msg_3["datetime"]

    for message_id, message in message_manager.items():
        assert messages[message_id] == message.to_dict()

######################################################################################################
# create/delete
######################################################################################################
def test_create_delete_project_and_childs(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    pytest.PROJECT_ID = project._backend.path
    action = project.require_action(pytest.ACTION_ID)
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents, overwrite=False)
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents, overwrite=False)

    load_database.delete_project(pytest.PROJECT_ID, remove_all_children=True)
    with pytest.raises(KeyError):
        load_database.get_project(pytest.PROJECT_ID)

    # remake project, then the "old" action and project_module should be deleted
    project = load_database.require_project(pytest.PROJECT_ID)
    with pytest.raises(KeyError):
        project.actions[pytest.ACTION_ID]
        project.modules[pytest.PROJECT_MODULE_ID]

    # remake action, then the "old" action_module should be deleted
    action = project.require_action(pytest.ACTION_ID)
    with pytest.raises(KeyError):
        action.modules[pytest.ACTION_MODULE_ID]


def test_create_delete_project_not_childs(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    pytest.PROJECT_ID = project._backend.path
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents, overwrite=True)

    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents, overwrite=True)
    with pytest.raises(OSError): # TODO this may be backend specific
        load_database.delete_project(pytest.PROJECT_ID)
    load_database.get_project(pytest.PROJECT_ID)

    # remake project, then the "old" action and action_module should be NOT be deleted
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.actions[pytest.ACTION_ID]
    action.modules[pytest.ACTION_MODULE_ID]



def test_create_project(load_database):
    load_database.require_project(pytest.PROJECT_ID)


def test_create_action(load_database):
    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.actions[pytest.ACTION_ID]


def test_create_action_module(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(pytest.ACTION_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)
    action.modules[pytest.ACTION_MODULE_ID]


def test_create_action_module_from_template(load_database):
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = load_database.require_project(pytest.PROJECT_ID)
    template = project.require_template(
        pytest.TEMPLATE_ID, template_contents)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, template=pytest.TEMPLATE_ID)
    module_contents = action.modules[pytest.ACTION_MODULE_ID].to_dict()
    assert module_contents == template_contents


def test_create_project_module(load_database):
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project.create_module(pytest.PROJECT_MODULE_ID, contents=module_contents, overwrite=True)
    project.modules[pytest.PROJECT_MODULE_ID]


def test_delete_action(load_database):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents, overwrite=True)

    time = datetime(2017, 6, 1, 21, 42, 20)
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    action.create_message(
        text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(
        text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    for attr in ['entities', 'users', 'tags']:
        setattr(action, attr, ['sub1', 'sub2'])
    assert len(list(action.modules.keys())) != 0
    project.delete_action(action.id)
    with pytest.raises(KeyError):
        project.actions[pytest.ACTION_ID]

    # remake and assert that all is deleted
    action = project.require_action(pytest.ACTION_ID)
    assert len(list(action.modules.keys())) == 0
    assert action_module.id not in action.modules
    for attr in ['entities', 'users', 'tags']:
        a = getattr(action, attr).data
        assert a is None
    assert len(action.messages) == 0


def test_delete_entity(load_database):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    message_manager = entity.messages
    entity_module = entity.create_module(pytest.ENTITY_MODULE_ID,
                                         contents=module_contents,
                                         overwrite=True)

    time = datetime(2017, 6, 1, 21, 42, 20)
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    entity.create_message(text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    entity.create_message(text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    for attr in ['entities', 'users', 'tags']:
        setattr(entity, attr, ['sub1', 'sub2'])
    assert len(list(entity.modules.keys())) != 0
    project.delete_entity(entity.id)
    with pytest.raises(KeyError):
        project.entities[pytest.ENTITY_ID]

    # remake and assert that all is deleted
    entity = project.require_entity(pytest.ENTITY_ID)
    assert len(list(entity.modules.keys())) == 0
    assert entity_module.id not in entity.modules
    for attr in ['users', 'tags']:
        a = getattr(entity, attr).data
        assert a is None
    assert len(entity.messages) == 0


def test_delete_entity_module(load_database):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    message_manager = entity.messages
    entity_module = entity.create_module(
        pytest.ENTITY_MODULE_ID, contents=module_contents, overwrite=True)
    entity_module = entity.create_module(
        pytest.ENTITY_MODULE_ID + '1', contents=module_contents, overwrite=True)

    # delete one
    entity.delete_module(pytest.ENTITY_MODULE_ID)

    with pytest.raises(KeyError):
        entity.modules[pytest.ENTITY_MODULE_ID]
    assert pytest.ENTITY_MODULE_ID + '1' in entity.modules


def test_delete_entity_message(load_database):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    message_manager = entity.messages

    time = datetime(2017, 6, 1, 21, 42, 20)

    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    msg_1_name = datetime.strftime(time, format)
    msg_2_name = datetime.strftime(time + timedelta(minutes=10), format)

    entity.create_message(
        text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    entity.create_message(
        text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    entity.delete_messages()
    with pytest.raises(KeyError):
        entity.messages[msg_1_name]
    assert msg_2_name not in entity.messages


def test_delete_action_module(load_database):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_entity(pytest.ACTION_ID)
    message_manager = action.messages
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents, overwrite=True)
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID + '1', contents=module_contents, overwrite=True)

    # delete one
    action.delete_module(pytest.ACTION_MODULE_ID)

    with pytest.raises(KeyError):
        action.modules[pytest.ACTION_MODULE_ID]
    assert pytest.ACTION_MODULE_ID + '1' in action.modules


def test_delete_action_message(load_database):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages

    time = datetime(2017, 6, 1, 21, 42, 20)

    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    msg_1_name = datetime.strftime(time, format)
    msg_2_name = datetime.strftime(time + timedelta(minutes=10), format)

    action.create_message(
        text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(
        text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    action.delete_messages()
    with pytest.raises(KeyError):
        action.messages[msg_1_name]
    assert msg_2_name not in action.messages


def test_delete_template(load_database):
    from datetime import datetime, timedelta
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = load_database.require_project(pytest.PROJECT_ID)
    template = project.require_template(
        pytest.TEMPLATE_ID, template_contents)
    template = project.require_template(
        pytest.TEMPLATE_ID + '1', template_contents)
    project.delete_template(pytest.TEMPLATE_ID)

    with pytest.raises(KeyError):
        project.templates[pytest.TEMPLATE_ID]
    assert pytest.TEMPLATE_ID + '1' in project.templates


def test_require_create_get_action(load_database):
    project = load_database.require_project(pytest.PROJECT_ID)

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


def test_fill_the_project(load_database):
    import quantities as pq
    from datetime import datetime, timedelta

    module_contents = {'species': {'value': 'rat'}}

    project = load_database.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}
    project_module = project.create_module(pytest.PROJECT_MODULE_ID,
                                           contents=module_contents,
                                           overwrite=True)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))

    time = datetime(2017, 6, 1, 21, 42, 20)
    msg_1 = {'text': 'sub1', 'user': 'usr1',
             'datetime': time}

    msg_2 = {'text': 'sub2', 'user': 'usr2',
             'datetime': time + timedelta(minutes=10)}

    action.create_message(
        text=msg_1["text"], user=msg_1["user"], datetime=msg_1["datetime"])
    action.create_message(
        text=msg_2["text"], user=msg_2["user"], datetime=msg_2["datetime"])

    orig_list = ['sub1', 'sub2']
    for attr in ['entities', 'users', 'tags']:
        prop_list = getattr(action, attr)
        assert isinstance(prop_list, expipe.core.PropertyList)
        prop_list.append('sub3')
        orig_list.append('sub3')
        setattr(action, attr, orig_list)
        prop_list.extend(['sub3'])
        orig_list.extend(['sub3'])
