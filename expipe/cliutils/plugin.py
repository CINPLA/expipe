# -*- coding: utf-8 -*-

"""Plugin system.

Code from http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures  # noqa

"""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import glob
import importlib
import os.path as op
from pkg_resources import load_entry_point
from six import with_metaclass
import platform
import sys

from .misc import _fullname



#------------------------------------------------------------------------------
# IPlugin interface
#------------------------------------------------------------------------------


class IPluginRegistry(type):
    plugins = []

    def __init__(cls, name, bases, attrs):
        if name != 'IPlugin':
            # print("Register plugin `%s`." % _fullname(cls))
            if _fullname(cls) not in (_fullname(_) for _ in IPluginRegistry.plugins):
                IPluginRegistry.plugins.append(cls)


class IPlugin(with_metaclass(IPluginRegistry)):
    """A class deriving from IPlugin can implement the following methods:

    * `attach_to_cli(cli)`: called when the CLI is created.

    """
    pass


def get_plugin(name):
    """Get a plugin class from its name."""
    for plugin in IPluginRegistry.plugins:
        print(plugin)
        if name in plugin.__name__:
            return plugin
    raise ValueError("The plugin %s cannot be found." % name)


#------------------------------------------------------------------------------
# Plugins discovery
#------------------------------------------------------------------------------

def load_plugins(modules):
    """Discover the plugin classes contained in Python files.

    Parameters
    ----------

    modules : list
        List of modules to load.

    Returns
    -------

    plugins : list
        List of plugin classes.

    """
    for modname in modules:
        try:
            importlib.import_module(modname)
        except ImportError as e:
            print('WARNING: Unable to import plugin. ' + str(e))
    return IPluginRegistry.plugins
