import pytest
from datetime import datetime
import expipe
expipe.ensure_testing()


def test_create_delete_project_and_childs(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
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
        action.get_module(pytest.MODULE_ID)


def test_create_delete_project_not_childs(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    expipe.delete_project(pytest.PROJECT_ID)
    with pytest.raises(NameError):
        expipe.get_project(pytest.PROJECT_ID)
    # remake project, then the "old" action and action_module should be NOT be deleted
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.get_action(pytest.ACTION_ID)
    action.get_module(pytest.MODULE_ID)


def test_create_project(teardown_project):
    expipe.require_project(pytest.PROJECT_ID)


def test_create_action(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    project.get_action(pytest.ACTION_ID)


def test_create_action_module(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    action.get_module(pytest.MODULE_ID)


def test_create_project_module(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    module_contents = {'test': {'value': 'youyo'}}
    project.require_module(pytest.MODULE_ID, contents=module_contents)
    project.get_module(pytest.MODULE_ID)


def test_module_get_require_equal_path(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    module_contents = {'test': {'value': 'youyo'}}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    project_module2 = project.get_module(pytest.MODULE_ID)
    assert project_module._db.path == project_module2._db.path

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    action_module2 = action.get_module(pytest.MODULE_ID)
    assert action_module._db.path == action_module2._db.path


def test_module_to_dict(teardown_project):
    from expipe.io.core import DictDiffer
    project = expipe.require_project(pytest.PROJECT_ID)
    module_contents = {'test': {'value': 'youyo'}}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)

    action = project.require_action(pytest.ACTION_ID)
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    module_dict = action_module.to_dict()
    for module_dict in [action_module.to_dict(), project_module.to_dict()]:
        d = DictDiffer(module_dict, module_contents)
        assert d.changed() == set()
        assert d.added() == set()
        assert d.removed() == set()

def test_action_attr(teardown_project):
        project = expipe.require_project(pytest.PROJECT_ID)
        action = project.require_action(pytest.ACTION_ID)
        for attr in ['subjects', 'messages', 'users', 'tags']:
            with pytest.raises(TypeError):
                setattr(action, attr, {'dict': 'I am'})
                setattr(action, attr, 'string I am')
        for attr in ['type', 'location']:
            setattr(action, attr, 'string I am')
            with pytest.raises(TypeError):
                setattr(action, attr, {'dict': 'I am'})
                setattr(action, attr, ['list I am'])
        from datetime import datetime
        action.datetime = datetime.now()
        with pytest.raises(TypeError):
            action.datetime = 'now I am'


def test_propertylist(teardown_project):
        project = expipe.require_project(pytest.PROJECT_ID)
        action = project.require_action(pytest.ACTION_ID)
        orig_list = ['sub1', 'sub2']
        for attr in ['subjects', 'messages', 'users', 'tags']:
            setattr(action, attr, orig_list)
            prop_list = getattr(action, attr)
            assert isinstance(prop_list, expipe.io.core.ProperyList)
            assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
            prop_list.append('sub3')
            orig_list.append('sub3')
            prop_list = getattr(action, attr)
            assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
            prop_list.extend(['sub3'])
            orig_list.extend(['sub3'])
            prop_list = getattr(action, attr)
            assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
            prop_list[2] = 'subsub'
            orig_list[2] = 'subsub'
            prop_list = getattr(action, attr)
            assert all(s1 == s2 for s1, s2 in zip(orig_list, prop_list))
            assert prop_list[2] == orig_list[2]
            orig_list = ['sub1', 'sub2']


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


def test_module_quantities(teardown_project):
    import quantities as pq
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    quan = [1, 2] * pq.s
    module_contents = {'quan': quan}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], pq.Quantity)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


def test_module_array(teardown_project):
    import numpy as np
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    quan = np.array([1, 2])
    module_contents = {'quan': quan}
    project_module = project.require_module(pytest.MODULE_ID,
                                            contents=module_contents)
    mod_dict = project_module.to_dict()
    assert isinstance(mod_dict['quan'], list)
    assert all(a == b for a, b in zip(quan, mod_dict['quan']))


def test_delete_action(teardown_project):
    project = expipe.require_project(pytest.PROJECT_ID)
    action = project.require_action(pytest.ACTION_ID)
    module_contents = {'test': {'value': 'youyo'}}
    action_module = action.require_module(pytest.MODULE_ID,
                                          contents=module_contents)
    orig_list = ['sub1', 'sub2']
    for attr in ['subjects', 'messages', 'users', 'tags']:
        setattr(action, attr, orig_list)
    project.delete_action(action.id)
    assert len(list(action.modules.keys())) == 0
    assert len(list(action_module.keys())) == 0
    with pytest.raises(NameError):
        project.get_action(pytest.ACTION_ID)
    # remake and assert that all is deleted
    action = project.require_action(pytest.ACTION_ID)
    for attr in ['subjects', 'messages', 'users', 'tags']:
        a = getattr(action, attr).data
        assert a is None

# TODO test delete project var and on delete
# TODO test messages and deletion
# TODO test to_json
# TODO test filerecord and Datafile and whatever it is for?
# TODO measure coverage
