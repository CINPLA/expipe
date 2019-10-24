import pytest
from unittest import mock
import expipe

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


def test_action_attr_raises(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    for attr in ['users', 'tags']:
        with pytest.raises(TypeError):
            setattr(action, attr, {'dict': 'I am'})
            setattr(action, attr, 'string I am')
            setattr(action, attr, [['string I am']])
    for attr in ['type', 'location']:
        setattr(action, attr, 'string I am')
        with pytest.raises(TypeError):
            setattr(action, attr, {'dict': 'I am'})
            setattr(action, attr, ['list I am'])
    with pytest.raises(TypeError):
        action.datetime = 'now I am'


def test_action_get_none_raises(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    with pytest.raises(TypeError):
        project.actions[None]


def test_entity_attr_raises(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)

    for attr in ['users', 'tags']:
        with pytest.raises(TypeError):
            setattr(entity, attr, {'dict': 'I am'})
            setattr(entity, attr, 'string I am')
            setattr(entity, attr, [['string I am']])
    for attr in ['type', 'location']:
        setattr(entity, attr, 'string I am')
        with pytest.raises(TypeError):
            setattr(entity, attr, {'dict': 'I am'})
            setattr(entity, attr, ['list I am'])
    with pytest.raises(TypeError):
        entity.datetime = 'now I am'



def test_action_attr_set_get(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    p = {
        'users': ['my'],
        'location': 'room',
        'type': 'recording',
        'datetime': datetime.now().replace(microsecond=0),
        'tags': ['e'],
        'entities': ['one']
    }
    for key, val in p.items():
        setattr(action, key, val)
    for key, val in p.items():
        gval = getattr(action, key)
        assert gval == val


def test_entitiy_attr_set_get(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    p = {
        'users': ['my'],
        'location': 'room',
        'type': 'recording',
        'datetime': datetime.now().replace(microsecond=0),
        'tags': ['e']
    }
    for key, val in p.items():
        setattr(entity, key, val)
    for key, val in p.items():
        gval = getattr(entity, key)
        assert gval == val

def test_property_list(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    orig_list = ['sub1', 'sub2']
    action.users = orig_list
    prop_list = action.users
    assert isinstance(prop_list, expipe.core.PropertyList)
    prop_list.append('sub3')
    orig_list.append('sub3')
    prop_list.extend(['sub4'])
    orig_list.extend(['sub4'])
    assert set(orig_list) == set(prop_list)
    reconstructed_prop_list = [prop_list[i] for i in range(len(prop_list))]
    assert 'sub4' in prop_list
    assert set(str(prop_list)) == set(str(orig_list))


def test_action_attr_list(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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


def test_action_attr_list_dtype(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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


# def test_module_manager(project_path):
    # pytest.PROJECT_ID = "retina"
    # project = expipe.core.Project(pytest.PROJECT_ID)
    # module_manager = project.modules
    # module = db_module_manager["project_modules"]["retina"]

    # assert project == module_manager.parent
    # assert module == module_manager.contents
    # assert all(k in module_manager for k in ("ret_1", "ret_2"))
    # assert set(list(module.keys())) == set(list(module_manager.keys()))

    # with pytest.raises(KeyError):
        # module_manager["ret_3"]

    # with pytest.raises(TypeError):
        # expipe.core.ModuleManager(parent=None)


def test_module_to_dict(project_path):
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents)

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)

    for module_dict in [action_module.contents, project_module.contents]:
        assert module_dict == module_contents


def test_module_quantities(project_path):
    import quantities as pq
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents)
    mod_contents = project_module.contents
    assert isinstance(mod_contents['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_contents['quan']))


def test_module_int_key(project_path):
    import numpy as np
    quan = 1
    module_contents = {1: quan}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action.modules[pytest.PROJECT_MODULE_ID] = module_contents
    assert action.modules[pytest.PROJECT_MODULE_ID][1] == quan


def test_module_array(project_path):
    import numpy as np
    quan = np.array([1, 2])
    module_contents = {'quan': quan}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents)
    mod_contents = project_module.contents
    assert isinstance(mod_contents['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_contents['quan']))


def test_module_get_require_equal_path(project_path):
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents)

    project_module2 = project.modules[pytest.PROJECT_MODULE_ID]
    assert project_module._backend.path == project_module2._backend.path

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    action_module2 = action.modules[pytest.ACTION_MODULE_ID]
    assert action_module._backend.path == action_module2._backend.path


def test_module_list(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=list_cont)
    mod_contents = project_module.contents
    assert isinstance(mod_contents, list)
    assert all(a == b for a, b in zip(list_cont, mod_contents))

    module_contents = {'list': list_cont}
    project.modules[pytest.PROJECT_MODULE_ID] = module_contents
    mod_contents = project.modules[pytest.PROJECT_MODULE_ID].contents
    assert isinstance(mod_contents['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_contents['list']))

    module_contents = {'dict_list': {'0': 'df', '1': 'd', '2': 's'}}
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    mod_contents = action_module.contents
    assert isinstance(mod_contents['dict_list'], dict)

    module_contents = {'almost_list1': {'0': 'df', '1': 'd', 'd': 's'}}
    action.modules[pytest.ACTION_MODULE_ID] = module_contents
    mod_contents = action.modules[pytest.ACTION_MODULE_ID].contents
    assert isinstance(mod_contents['almost_list1'], dict)
    assert module_contents == mod_contents, '{}, {}'.format(module_contents, mod_contents)

    module_contents = {'dict_list': {0: 'df', 1: 'd', 2: 's'}}
    action.modules[pytest.ACTION_MODULE_ID] = module_contents
    mod_contents = action.modules[pytest.ACTION_MODULE_ID].contents
    assert isinstance(mod_contents['dict_list'], dict)


def test_modify_module_view(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=list_cont)
    mod_contents = project_module.contents
    assert isinstance(mod_contents, list)
    assert all(a == b for a, b in zip(list_cont, mod_contents))

    module_contents = {'list': list_cont}
    project.modules[pytest.PROJECT_MODULE_ID] = module_contents
    mod_contents = project_module.contents
    assert isinstance(mod_contents['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_contents['list']))


def test_create_deep_module_content(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    with pytest.raises(KeyError):
        project.modules[pytest.PROJECT_MODULE_ID]['eh']
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents={'eh': {}})
    project_module['eh']['ehhh'] = {}
    project_module['eh']['ehhh']['ehhhh'] = 'stuff'
    print(project_module['eh']['ehhh'])
    assert project_module['eh']['ehhh'] == {'ehhhh': 'stuff'}
    assert project_module['eh']['ehhh']['ehhhh'] == 'stuff'
    assert 'ehhhh' in project_module['eh']['ehhh']


######################################################################################################
# Message and MessageManager
######################################################################################################

# TODO should check that we get a dict that contains the same items
def test_entity_messages_setter(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ACTION_ID)
    message_manager = entity.messages

    assert len(message_manager) == 0

    time = datetime(2017, 6, 1, 21, 42, 20)
    text = "my message"
    user = "user1"

    msg_object = entity.create_message(text=text, user=user, datetime=time)
    with pytest.raises(KeyError):
        entity.create_message(text=text, user=user, datetime=time)


def test_action_messages_setter(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages

    assert len(message_manager) == 0

    time = datetime(2017, 6, 1, 21, 42, 20)
    text = "my message"
    user = "user1"

    msg_1 = {'text': text, 'user': user, 'datetime': time}

    messages = [msg_1]
    msg_object = action.create_message(text=text, user=user, datetime=time)
    with pytest.raises(KeyError):
        action.create_message(text=text, user=user, datetime=time)

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


def test_action_messages_dtype(project_path):
    from datetime import datetime, timedelta
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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


def test_change_message(project_path):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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
        assert messages[message_id] == message.contents

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
        assert messages[message_id] == message.contents


def test_nested_module(project_path):
    module_contents = {'species': {}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    action_module['species']['value'] = 'rat'
    action_module['species']['name'] = 'peter'
    assert action_module['species']['value'] == 'rat'
    assert action_module['species'].contents == {'value': 'rat', 'name': 'peter'}
    assert action_module['species'] == {'value': 'rat', 'name': 'peter'}


def test_action_data(project_path):
    data_path = 'path/to/my/data'
    data_path1 = 'path/to/my/data/1'

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    action.users = ['Mikkel']
    assert action.users == ['Mikkel']
    action.data['main'] = data_path
    action.data['one'] = data_path1
    assert action.data['main'] == data_path
    assert action.data['one'] == data_path1
    assert action.users == ['Mikkel']


def test_isinstance_module(project_path):
    module_contents = {'species': {}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    assert isinstance(action_module, expipe.core.Module)


def test_isinstance_template(project_path):
    template_contents = {'species': {}, 'identifier': 'yoyo'}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)

    template = project.create_template(
        pytest.TEMPLATE_ID, contents=template_contents)
    assert isinstance(template, expipe.core.Template)

######################################################################################################
# create/delete
######################################################################################################
def test_create_project(project_path):
    expipe.create_project(project_path, pytest.PROJECT_ID)


def test_create_project_raises_exist_but_no_project(project_path):
    project_path.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        expipe.create_project(project_path, pytest.PROJECT_ID)


def test_require_project(project_path):
    expipe.require_project(project_path, pytest.PROJECT_ID)


def test_create_get_project(project_path):
    with pytest.raises(KeyError):
        expipe.get_project(project_path)
    expipe.create_project(project_path, pytest.PROJECT_ID)
    expipe.get_project(project_path)


def test_project_config(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    config = {
        "database_version": 2,
        "type": "project",
        "project": pytest.PROJECT_ID
    }
    for key in config.keys():
        assert project.config[key] == config[key]


def test_create_project_inside_project_raises(project_path):
    expipe.create_project(project_path, pytest.PROJECT_ID)
    with pytest.raises(KeyError):
        expipe.create_project(project_path / 'new', pytest.PROJECT_ID + '1')


def test_create_action(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    action = project.create_action(pytest.ACTION_ID)
    project.actions[pytest.ACTION_ID]


def test_create_empty_raises(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    with pytest.raises(ValueError):
        project.create_action('')
        project.create_entity('')


def test_create_None_raises(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    with pytest.raises(TypeError):
        project.create_template(None, {})
        project.create_action(None)
        project.create_entity(None)
        project.create_module(None)
    action = project.create_action(pytest.ACTION_ID)
    project.actions[pytest.ACTION_ID]
    with pytest.raises(TypeError):
        action.create_module(None)


def test_requre_action(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.require_action(pytest.ACTION_ID)


def test_create_entity(project_path):
    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    entity = project.create_entity(pytest.ENTITY_ID)
    project.entities[pytest.ENTITY_ID]
    with pytest.raises(KeyError):
        project.create_entity(pytest.ENTITY_ID)


def test_require_entity(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    project.require_entity(pytest.ENTITY_ID)


def test_create_action_module(project_path):
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    # contents cannot be string
    with pytest.raises(TypeError):
        action.create_module(
            pytest.ACTION_MODULE_ID, contents='module_contents')
    # contents can be dict
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    assert action_module == module_contents

    module_contents = ['species', 1]
    # contents can be list
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID + '_1', contents=module_contents)
    assert action_module == module_contents
    import numpy as np
    module_contents = np.array(['species', 1])
    # contents can be array
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID + '_2', contents=module_contents)
    assert action_module == module_contents.tolist()


def test_create_template(project_path):
    template_contents = {
        'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    # no identifier
    with pytest.raises(ValueError):
        template = project.require_template(
            pytest.TEMPLATE_ID, template_contents)

    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}
    template = project.require_template(
        pytest.TEMPLATE_ID, template_contents)
    # cannot overwrite with create
    with pytest.raises(KeyError):
        template = project.create_template(
            pytest.TEMPLATE_ID, template_contents)
    # require gets it
    template = project.require_template(
        pytest.TEMPLATE_ID)

def test_create_action_module_from_template(project_path):
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    template = project.require_template(
        pytest.TEMPLATE_ID, template_contents)
    action = project.require_action(pytest.ACTION_ID)

    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, template=pytest.TEMPLATE_ID)
    module_contents = action.modules[pytest.ACTION_MODULE_ID].contents
    assert module_contents == template_contents


def test_create_action_module_from_template_no_module_name(project_path):
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = expipe.create_project(project_path, pytest.PROJECT_ID)
    template = project.create_template(pytest.TEMPLATE_ID, template_contents)
    action = project.create_action(pytest.ACTION_ID)
    action_module = action.create_module(template=pytest.TEMPLATE_ID)
    assert action.modules[pytest.TEMPLATE_ID] == template_contents


def test_require_action_module_from_template_no_module_name(project_path):
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    template = project.require_template(pytest.TEMPLATE_ID, template_contents)
    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(template=pytest.TEMPLATE_ID)
    assert action.modules[pytest.TEMPLATE_ID] == template_contents


def test_create_retrieve_project_module(project_path):
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    project.create_module(pytest.PROJECT_MODULE_ID, contents=module_contents)
    assert project.modules[pytest.PROJECT_MODULE_ID] == module_contents
    project.require_module(pytest.PROJECT_MODULE_ID)
    with pytest.raises(KeyError):
        project.create_module(
            pytest.PROJECT_MODULE_ID, contents=module_contents)


def test_set_project_module_deep(project_path):
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    mod = project.create_module(pytest.PROJECT_MODULE_ID, contents=module_contents)
    project.modules[pytest.PROJECT_MODULE_ID]['species']['value'] = 'mouse'
    assert mod['species']['value'] == 'mouse'


def test_iterate_module_contents(project_path):
        module_contents = {
            'species': {'value': 'rat'},
        }

        project = expipe.require_project(project_path, pytest.PROJECT_ID)
        action = project.require_action(pytest.ACTION_ID)

        mod = project.create_module(pytest.PROJECT_MODULE_ID, contents=module_contents)
        for mod_cont, true_cont in zip(mod.values(), module_contents.values()):
            assert mod_cont == true_cont


def test_action_has_no_contents(project_path):
        project = expipe.require_project(project_path, pytest.PROJECT_ID)
        action = project.require_action(pytest.ACTION_ID)
        with pytest.raises(AttributeError):
            action.contents


def test_delete_action(project_path):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    message_manager = action.messages
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)

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


def test_delete_entity(project_path):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    message_manager = entity.messages
    entity_module = entity.create_module(
        pytest.ENTITY_MODULE_ID, contents=module_contents)

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


def test_delete_entity_module(project_path):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    entity = project.require_entity(pytest.ENTITY_ID)
    message_manager = entity.messages
    entity_module = entity.create_module(
        pytest.ENTITY_MODULE_ID, contents=module_contents)
    entity_module = entity.create_module(
        pytest.ENTITY_MODULE_ID + '1', contents=module_contents)

    # delete one
    entity.delete_module(pytest.ENTITY_MODULE_ID)

    with pytest.raises(KeyError):
        entity.modules[pytest.ENTITY_MODULE_ID]
    assert pytest.ENTITY_MODULE_ID + '1' in entity.modules


def test_delete_entity_message(project_path):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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


def test_delete_action_module(project_path):
    from datetime import datetime, timedelta
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_entity(pytest.ACTION_ID)
    message_manager = action.messages
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID, contents=module_contents)
    action_module = action.create_module(
        pytest.ACTION_MODULE_ID + '1', contents=module_contents)

    # delete one
    action.delete_module(pytest.ACTION_MODULE_ID)

    with pytest.raises(KeyError):
        action.modules[pytest.ACTION_MODULE_ID]
    assert pytest.ACTION_MODULE_ID + '1' in action.modules


def test_delete_action_message(project_path):
    from datetime import datetime, timedelta
    format = expipe.core.datetime_key_format
    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
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


def test_delete_template(project_path):
    from datetime import datetime, timedelta
    template_contents = {
        'species': {'value': 'rat'},
        'identifier': pytest.TEMPLATE_ID}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    template = project.require_template(
        pytest.TEMPLATE_ID, template_contents)
    template = project.require_template(
        pytest.TEMPLATE_ID + '1', template_contents)
    project.delete_template(pytest.TEMPLATE_ID)

    with pytest.raises(KeyError):
        project.templates[pytest.TEMPLATE_ID]
    assert pytest.TEMPLATE_ID + '1' in project.templates


def test_require_create_get_action(project_path):
    project = expipe.require_project(project_path, pytest.PROJECT_ID)

    # Get a non-existing action
    with pytest.raises(KeyError):
        action = project.actions[pytest.ACTION_ID]

    # Create an existing action
    action = project.create_action(pytest.ACTION_ID)
    with pytest.raises(KeyError):
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


def test_fill_the_project(project_path):
    import quantities as pq
    from datetime import datetime, timedelta

    module_contents = {'species': {'value': 'rat'}}

    project = expipe.require_project(project_path, pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)

    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}
    project_module = project.create_module(
        pytest.PROJECT_MODULE_ID, contents=module_contents)
    mod_contents = project_module.contents
    assert isinstance(mod_contents['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_contents['quan']))

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
