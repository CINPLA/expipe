import pytest
from datetime import datetime, timedelta
import expipe
expipe.ensure_testing()


# def test_create_delete_project_and_childs(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     action_module = action.require_module(pytest.MODULE_ID,
#                                           contents=module_contents)
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#     expipe.delete_project(pytest.PROJECT_ID, remove_all_childs=True)
#     with pytest.raises(NameError):
#         expipe.get_project(pytest.PROJECT_ID)
#     # remake project, then the "old" action and project_module should be deleted
#     project = expipe.require_project(pytest.PROJECT_ID)
#     with pytest.raises(NameError):
#         project.get_action(pytest.ACTION_ID)
#         project.get_module(pytest.MODULE_ID)
#     # remake action, then the "old" action_module should be deleted
#     action = project.require_action(pytest.ACTION_ID)
#     with pytest.raises(NameError):
#         action.get_module(pytest.MODULE_ID)
#
#
# def test_create_delete_project_not_childs(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     action_module = action.require_module(pytest.MODULE_ID,
#                                           contents=module_contents)
#     expipe.delete_project(pytest.PROJECT_ID)
#     with pytest.raises(NameError):
#         expipe.get_project(pytest.PROJECT_ID)
#     # remake project, then the "old" action and action_module should be NOT be deleted
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.get_action(pytest.ACTION_ID)
#     action.get_module(pytest.MODULE_ID)
#
#
# def test_create_project(teardown_project):
#     expipe.require_project(pytest.PROJECT_ID)
#
#
# def test_create_action(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     project.get_action(pytest.ACTION_ID)
#
#
# def test_create_action_module(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     action_module = action.require_module(pytest.MODULE_ID,
#                                           contents=module_contents)
#     action.get_module(pytest.MODULE_ID)
#
#
# def test_create_project_module(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     project.require_module(pytest.MODULE_ID, contents=module_contents)
#     project.get_module(pytest.MODULE_ID)
#
#
# def test_module_get_require_equal_path(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#     project_module2 = project.get_module(pytest.MODULE_ID)
#     assert project_module._db.path == project_module2._db.path
#
#     action = project.require_action(pytest.ACTION_ID)
#     action_module = action.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#     action_module2 = action.get_module(pytest.MODULE_ID)
#     assert action_module._db.path == action_module2._db.path
#
#
# def test_module_to_dict(teardown_project):
#     from expipe.io.core import DictDiffer
#     project = expipe.require_project(pytest.PROJECT_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#
#     action = project.require_action(pytest.ACTION_ID)
#     action_module = action.require_module(pytest.MODULE_ID,
#                                           contents=module_contents)
#     module_dict = action_module.to_dict()
#     for module_dict in [action_module.to_dict(), project_module.to_dict()]:
#         d = DictDiffer(module_dict, module_contents)
#         assert d.changed() == set()
#         assert d.added() == set()
#         assert d.removed() == set()
#
#
def test_module_list(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    list_cont = ['list I am', 1]
    with pytest.raises(TypeError):
        project_module = project.require_module(pytest.MODULE_ID,
                                                contents=list_cont)

    module_contents = {'list': list_cont}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['list'], list)
    assert all(a == b for a, b in zip(list_cont, mod_dict['list']))

    module_contents = {'is_list': {'1': 'df', '2': 'd', '3': 's'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['is_list'], list)

    module_contents = {'almost_list1': {'1': 'df', '2': 'd', 'd': 's'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                            contents=module_contents,
                                            overwrite=True)
    mod_dict = action_module.to_dict()
    assert isinstance(mod_dict['almost_list1'], dict)
    diff = expipe.io.core.DictDiffer(module_contents, mod_dict)
    assert diff.changed() == set(), '{}, {}'.format(module_contents, mod_dict)

    # TODO make this go through
    # module_contents = {'almost_list2': {'1': 'df', '2': 'd', '5': 's'}}
    # action_module = action.require_module(pytest.MODULE_ID,
    #                                         contents=module_contents,
    #                                         overwrite=True)
    # mod_dict = action_module.to_dict()
    # assert isinstance(mod_dict['almost_list2'], dict)
    # diff = expipe.io.core.DictDiffer(module_contents, mod_dict)
    # assert diff.changed() == set(), '{}, {}'.format(module_contents, mod_dict)
#
#
# def test_module_quantities(teardown_project):
#     import quantities as pq
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     quan = [1, 2] * pq.s
#     module_contents = {'quan': quan}
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#     mod_dict = project_module.to_dict()
#     assert isinstance(mod_dict['quan'], pq.Quantity)
#     assert all(a == b for a, b in zip(quan, mod_dict['quan']))
#
#
# def test_module_array(teardown_project):
#     import numpy as np
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     quan = np.array([1, 2])
#     module_contents = {'quan': quan}
#     project_module = project.require_module(pytest.MODULE_ID,
#                                             contents=module_contents)
#     mod_dict = project_module.to_dict()
#     assert isinstance(mod_dict['quan'], list)
#     assert all(a == b for a, b in zip(quan, mod_dict['quan']))


# def test_delete_action(teardown_project):
#     project = expipe.require_project(pytest.PROJECT_ID)
#     action = project.require_action(pytest.ACTION_ID)
#     module_contents = {'test': {'value': 'youyo'}}
#     action_module = action.require_module(pytest.MODULE_ID,
#                                           contents=module_contents)
#     mes = action.messages
#     time = datetime(2017, 6, 1, 21, 42, 20)
#     mes.datetimes = [time, time - timedelta(minutes=1)]
#     mes.users = ['us1', 'us2']
#     mes.messages = ['mes1', 'mes2']
#
#     for attr in ['subjects', 'users', 'tags']:
#         setattr(action, attr, ['sub1', 'sub2'])
#     project.delete_action(action.id)
#     with pytest.raises(NameError):
#         project.get_action(pytest.ACTION_ID)
#     # remake and assert that all is deleted
#     action = project.require_action(pytest.ACTION_ID)
#     assert len(list(action.modules.keys())) == 0
#     assert len(list(action_module.keys())) == 0
#     for attr in ['subjects', 'users', 'tags']:
#         a = getattr(action, attr).data
#         assert a is None
#     assert len(action.messages.messages) == 0
#     assert len(action.messages.datetimes) == 0
#     assert len(action.messages.users) == 0


# def test_action_attr(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         for attr in ['subjects', 'users', 'tags']:
#             with pytest.raises(TypeError):
#                 setattr(action, attr, {'dict': 'I am'})
#                 setattr(action, attr, 'string I am')
#         for attr in ['type', 'location']:
#             setattr(action, attr, 'string I am')
#             with pytest.raises(TypeError):
#                 setattr(action, attr, {'dict': 'I am'})
#                 setattr(action, attr, ['list I am'])
#         action.datetime = datetime.now()
#         with pytest.raises(TypeError):
#             action.datetime = 'now I am'


# def test_action_attr_list(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         orig_list = ['sub1', 'sub2']
#         for attr in ['subjects', 'users', 'tags']:
#             setattr(action, attr, orig_list)
#             prop_list = getattr(action, attr)
#             assert isinstance(prop_list, expipe.io.core.ProperyList)
#             assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
#             prop_list.append('sub3')
#             orig_list.append('sub3')
#             prop_list = getattr(action, attr)
#             assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
#             prop_list.extend(['sub3'])
#             orig_list.extend(['sub3'])
#             prop_list = getattr(action, attr)
#             assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
#             prop_list[2] = 'subsub'
#             orig_list[2] = 'subsub'
#             prop_list = getattr(action, attr)
#             assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
#             assert prop_list[2] == orig_list[2]
#             orig_list = ['sub1', 'sub2']


# def test_action_attr_list_dtype(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         for attr in ['subjects', 'users', 'tags']:
#             with pytest.raises(TypeError):
#                 setattr(action, attr, ['sub1', 'sub2', 1])
#             with pytest.raises(TypeError):
#                 setattr(action, attr, ['sub1', 'sub2', ['s']])
#             setattr(action, attr, ['sub1', 'sub2'])
#             prop_list = getattr(action, attr)
#             with pytest.raises(TypeError):
#                 prop_list.append(1)
#             with pytest.raises(TypeError):
#                 prop_list.extend([1])
#             with pytest.raises(TypeError):
#                 prop_list[2] = 1


# def test_action_messages_list_setter(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         mes = action.messages
#         messages = ['mes1', 'mes2']
#         time = datetime(2017, 6, 1, 21, 42, 20)
#         datetimes = [time, time - timedelta(minutes=1)]
#         users = ['us1', 'us2']
#         mes.datetimes = datetimes
#         mes.users = users
#         mes.messages = messages
#         assert isinstance(mes.messages, expipe.io.core.ProperyList)
#         assert isinstance(mes.users, expipe.io.core.ProperyList)
#         assert isinstance(mes.datetimes, expipe.io.core.ProperyList)
#         mes.messages.append('sub3')
#         messages.append('sub3')
#         mes.messages.extend(['sub3'])
#         messages.extend(['sub3'])
#         mes.messages[2] = 'subsub'
#         messages[2] = 'subsub'
#
#         mes.datetimes.append(time - timedelta(minutes=3))
#         datetimes.append(time - timedelta(minutes=3))
#         mes.datetimes.extend([time - timedelta(minutes=2)])
#         datetimes.extend([time - timedelta(minutes=2)])
#         mes.datetimes[2] = time - timedelta(minutes=11)
#         datetimes[2] = time - timedelta(minutes=11)
#
#         mes.users.append('sub3')
#         users.append('sub3')
#         mes.users.extend(['sub3'])
#         users.extend(['sub3'])
#         mes.users[2] = 'subsub'
#         users[2] = 'subsub'
#         assert all(s1 == s2 for s1, s2 in zip(messages, mes.messages))
#         assert all(s1 == s2 for s1, s2 in zip(datetimes, mes.datetimes))
#         assert all(s1 == s2 for s1, s2 in zip(users, mes.users))
#
#
# def test_action_messages_list_no_setter(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         mes = action.messages
#         messages = []
#         time = datetime(2017, 6, 1, 21, 42, 20)
#         datetimes = []
#         users = []
#         mes.messages.append('sub3')
#         messages.append('sub3')
#         mes.messages.extend(['sub3'])
#         messages.extend(['sub3'])
#         mes.messages[1] = 'subsub'
#         messages[1] = 'subsub'
#         mes.datetimes.append(time - timedelta(minutes=3))
#         datetimes.append(time - timedelta(minutes=3))
#         mes.datetimes.extend([time - timedelta(minutes=2)])
#         datetimes.extend([time - timedelta(minutes=2)])
#         mes.datetimes[1] = time - timedelta(minutes=11)
#         datetimes[1] = time - timedelta(minutes=11)
#
#         mes.users.append('sub3')
#         users.append('sub3')
#         mes.users.extend(['sub3'])
#         users.extend(['sub3'])
#         mes.users[1] = 'subsub'
#         users[1] = 'subsub'
#         assert all(s1 == s2 for s1, s2 in zip(messages, mes.messages))
#         assert all(s1 == s2 for s1, s2 in zip(datetimes, mes.datetimes)), '{}, {}'.format(datetimes, mes.datetimes)
#         assert all(s1 == s2 for s1, s2 in zip(users, mes.users))
#
#
# def test_action_messages_dtype(teardown_project):
#         project = expipe.require_project(pytest.PROJECT_ID)
#         action = project.require_action(pytest.ACTION_ID)
#         mes = action.messages
#         time = datetime(2017, 6, 1, 21, 42, 20)
#         with pytest.raises(TypeError):
#             mes.datetimes = [1, time - timedelta(minutes=1)]
#             mes.users = ['us1', 1]
#             mes.messages = ['mes1', 1]
#         with pytest.raises(TypeError):
#             mes.messages.append(1)
#             mes.messages.extend([1])
#             mes.messages[2] = 1
#
#             mes.datetimes.append('time - timedelta(minutes=3)')
#             mes.datetimes.extend(['time - timedelta(minutes=2)'])
#             mes.datetimes[2] = 'time - timedelta(minutes=11)'
#
#             mes.users.append(1)
#             mes.users.extend([1])
#             mes.users[2] = 1


# TODO test delete project var and on delete
# TODO test messages and deletion
# TODO test to_json
# TODO test filerecord and Datafile and whatever it is for?
# TODO measure coverage
# TODO test how lists are identified and read e.g. can you give {1:'d', 2: 'd', 'd':2}
# TODO test if you can give template identifier which si not unique
