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

Create a new project if it does not exist with `require_project`:

.. doctest::

    >>> import expipe.io
    >>> project = expipe.io.require_project("test")

A project can contain a number of actions and subjects.

Actions
-------

Actions are events that are performed during a project.
An action can be an experiment or any preparation for an experiment.

To create an action on the project or return an existing action if it already
exists, use `project.require_action`:

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
    >>> users.update('Peter')
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
    >>> action.require_module(name="tracking", contents=contents)
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
