.. _plugin_page:

****************
Making a plugin
****************

This section describes how to make a plugin for the expipe-cli package.
For the complete example; see https://github.com/CINPLA/expipe-plugin-example.

In order to make a plugin for the comman line interface you need to make a
python package.

Begin by making a folder named ``my_plugin`` with a module, let's call it
``my_module.py`` containing::

  from expipecli.utils import IPlugin
  import click


  class MyPlugin(IPlugin):
      """Create the `expipe do-incredible-stuff` command."""
      def attach_to_cli(self, cli):
          @cli.command('do-incredible-stuff')
          @click.argument('stuff', type=click.STRING)
          def incredible(stuff):
              '''
              Do incredible stuff

              COMMAND: stuff
              '''

              print('incredible', stuff)


The folder ``my_plugin`` must also contain a file ``__init__.py`` containing::


  from .my_module import MyPlugin


Finally in ``my_plugin`` make a module called ``my_plugin_loader`` with the
following content.::

  # This imports all plugins when loading expipe.
  import my_plugin


  def reveal():
      pass

In the root directory you need a ``setup.py`` file with the
following minimum contents, note that the entry point must begin with
``plugin-expipe`` which is absolutely necesessary.::

  from setuptools import setup

  from setuptools import setup, find_packages

  setup(
      name="my-plugin",
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'plugin-expipe-superduper = my_plugin.my_plugin_loader:reveal'
          ]
      }
  )

You are good to go, you should now be able to::

  $ python setup.py develop
  $ expipe do-incredible-stuff "is my incredible stuff"
