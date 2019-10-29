.. _plugin_page:

****************
Making a plugin
****************

This section describes how to make a plugin for the Expipe command line interface (CLI).
For the complete example; see https://github.com/CINPLA/expipe-plugin-example.

In order to make a plugin for the comman line interface you first need to make a
python package.

Begin by making a folder named :code:`my_plugin` with a module, let's call it
:code:`my_module.py` containing:

.. code-block:: python


  from expipe.cliutils import IPlugin
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

              print('INCREDIBLE', stuff)


The folder :code:`my_plugin` must also contain a file :code:`__init__.py` containing:

.. code-block:: python

  from .my_module import MyPlugin


Finally in :code:`my_plugin` make a module called :code:`my_plugin_loader` with the
following content:

.. code-block:: python

  # This imports all plugins when loading expipe.
  import my_plugin


  def reveal():
      pass

In the root directory you need a :code:`setup.py` file with the
following minimum contents, note that the entry point MUST begin with
:code:`plugin-expipe`:

.. code-block:: python

  from setuptools import setup

  from setuptools import setup, find_packages

  setup(
      name="my_plugin",
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'plugin-expipe-superduper = my_plugin.my_plugin_loader:reveal'
          ]
      }
  )

After the plugin package is ready, all you need to do is to install it and add it to the Expipe environment:

.. code-block:: bash

  >>> python setup.py develop
  >>> expipe config global --add plugin my_plugin

Finally, you can run your new incredible plugin with expipe:

.. code-block:: bash

  >>> expipe do-incredible-stuff "is my incredible stuff!"

.. parsed-literal::

    INCREDIBLE is my incredible stuff!

