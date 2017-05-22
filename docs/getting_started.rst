Getting started
---------------

To get started with Expipe, a Firebase_ database needs to be set up.
Further, a shared storage space should be configured and mounted on all
computers using Expipe.
However, while debugging, a local folder can be used for storage.

.. _Firebase: https://firebase.google.com

After setting up a Firebase database, expipe needs to be configured.
This is done by importing expipe and running `expipe.configure`.
If you are an expipe user, please see the website of your lab for instructions
on how to run this command.
If you are involved in CINPLA, please see the
`CINPLA setup page <https://github.com/CINPLA/expipe-plugin-cinpla/wiki/Setup>`_.

    >>> import expipe
    >>> expipe.configure( # doctest: +SKIP
    ...     data_path="",
    ...     email="",
    ...     password="",
    ...     url_prefix="",
    ...     api_key=""
    ... )

If you install the `expipe-cli` package you can configure expipe using the
command line::

    $ expipe configure --data-path /path/to/data --email my@email.com ...


Templates
---------

In order to prime your metadatabase you can begin with adding templates. If
you are using `expipe` for neuroscience you can add
`odML terminologies <https://github.com/G-Node/odml-terminologies>`_
with the sript found in utils ``convert_odml_terminologies.py``. Clone the
repository and give the script it's path::

  $ convert_odml_terminologies.py path/to/odml_repo

To view the templates we encourage you to use the ``expipe-browser``.

Project
--------

Create a new project if it does not exist with ``require_project``:

.. doctest::

    >>> import expipe.io
    >>> project = expipe.io.require_project("test")

A project can contain a number of actions and modules.

Actions
-------

Actions are events that are performed during a project.
An action can be an experiment or any preparation for an experiment.

To create an action on the project or return an existing action if it already
exists, use ``project.require_action``:

.. doctest::

    >>> action = project.require_action("something")

Action attributes
-----------------

To give actions easily searchable properties you can add `Tags`, `Users`,
`Subjects` and `Datetime`

.. doctest::

    >>> from datetime import datetime
    >>> action.tags = ['place cell', 'familiar environment']
    >>> action.datetime = datetime.now()
    >>> users = action.users
    {}
    >>> users.update({'Peter': 'true'})
    >>> action.users = users

Modules
-------

Actions have multiple properties such as the type,
location, users, tags and subjects.
If you want to expand an action with more information,
you can use modules.
Modules can hold arbitrary information about the action and can be predefined by
using templates to make it easy to add the same information to multiple actions.
Ideally, templates should be designed in the beginning of a project to define
what should be registered in each action.

To add a module to an action, use `require_module`.
The function takes an optional `template` parameter:

.. doctest::

    >>> tracking = action.require_module("tracking", template="tracking")

We recommend using `expipe-browser` to edit and browse module values.

If you are not using templates you may also create modules using dictionaries

.. doctest::

    >>> import quantities
    >>> tracking = {'box_shape': {'value': 'square'}}
    >>> action.require_module(name="tracking", contents=tracking)
    >>> elphys = {'depth': 2 * pq.um, }
    >>> action.require_module(name="electrophysiology", contents=elphys)

You can loop through modules in an action

    >>> for name, val in action.modules.items():
    >>>     if name == 'electrophysiology':
    >>>         print(val['depth'])
    2 um

To further retrieve and edit the values of a module, you can use `module.to_dict()`:

.. doctest::

    >>> tracking = action.require_module(name="tracking")
    >>> print(tracking.to_dict())
    {'box_shape': {'value': 'square'}}

From template to module
-----------------------

In order to use a template and add it as a module to an `action` use
``action.require_module``:

.. doctest::

  >>> dac = action.require_module(template='hardware_dac')

Now, the template `hardware_dac` is added to your action as a module and you
also have it locally stored in the variable ``dac``. To retrieve ``dac`` keys
and values use ``to_dict``:

.. doctest::

  >>> dac_dict = dac.to_dict()
  >>> print(dac_dict.keys())
  >>> print(dac_dict.values())

You may also view the module as ``.json`` by using the command ``to_json``:

.. doctest::

  >>> dac.to_json()

To furter change its values and upload them to Firebase:

.. doctest::

  >>> dac_dict['gain'] = {'value': 20}
  >>> action.require_module(name='hardware_dac', contents=dac_dict)
