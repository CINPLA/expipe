import pytest


def test_added(setup_dict):
    d = setup_dict
    assert d.added() == set(['d'])


def test_removed(setup_dict):
    d = setup_dict
    assert d.removed() == set(['c'])


def test_changed(setup_dict):
    d = setup_dict
    assert d.changed() == set(['b'])


def test_unchanged(setup_dict):
    d = setup_dict
    assert d.unchanged() == set(['a'])
