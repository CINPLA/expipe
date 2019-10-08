Getting started
---------------

Expipe can be used to manage multiple projects.
Each project consists of collections of actions, entities, templates and project modules.

Project
--------

Create a new project if it does not exist with ``require_project``:

.. doctest::

    >>> import expipe
    >>> project = expipe.require_project("test")

The default backend for Expipe uses the filesystem.
In this case, the above command will create a folder named `test` in your current
working directory.
Other backends will create a backend-specific project in its database.



Actions
-------

Actions are events that are performed during a project.
An action can be an experiment, preparations for an experiment, or an analysys performed after
an experiment.

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
    >>> action.location = 'here'
    >>> action.type = 'Recording'
    >>> action.subjects = ['rat1']
    >>> action.users = ['Peter', 'Mary']


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
The function takes an optional `template` parameter::

    tracking = action.require_module("tracking", template="tracking")

We recommend using `expipe-browser` to edit and browse module values.

If you are not using templates you may also create modules using dictionaries

.. doctest::

    >>> import quantities as pq
    >>> tracking_contents = {'box_shape': {'value': 'square'}}
    >>> tracking_module = action.require_module(name="tracking",
    ...                                         contents=tracking_contents)
    >>> elphys_contents = {'depth': 2 * pq.um, }
    >>> elphys_module = action.require_module(name="electrophysiology",
    ...                                       contents=elphys_contents)

You can loop through modules in an action

    >>> for name, val in action.modules.items():
    ...     if name == 'electrophysiology':
    ...         print(val['depth'])
    2.0 um

To further retrieve and edit the values of a module, you can use `module.to_dict()`:

.. doctest::

    >>> tracking = action.require_module(name="tracking")
    >>> print(tracking.to_dict())
    OrderedDict([('box_shape', {'value': 'square'})])

From template to module
-----------------------

To upload a template you can write it as a ``dict`` and use
``require_template``.

.. doctest::

  >>> daq_contents = {
  ...    "channel_count": {
  ...         "definition": "The number of input channels of the DAQ-device.",
  ...         "value": "64"}}
  >>> expipe.require_template(template='hardware_daq',
  ...                         contents=daq_contents)


In order to use a template and add it as a module to an `action` use
``action.require_module``:

.. doctest::

  >>> daq = action.require_module(template='hardware_daq')

Now, the template `hardware_daq` is added to your action as a module and you
also have it locally stored in the variable ``daq``. To retrieve ``daq`` keys
and values use ``to_dict``:

.. doctest::

  >>> daq_dict = daq.to_dict()
  >>> print(daq_dict.keys())
  odict_keys(['channel_count'])
  >>> print(daq_dict.values())
  odict_values([{'definition': 'The number of input channels of the DAQ-device.', 'value': '64'}])

Messages
--------

Actions have multiple properties such as the type,
location, users, tags and subjects.
If you want to expand an action with notes and messages,
you can use messages. Messages are annotations from users that are involved
with an action. To add a message:

.. doctest::

    >>> from datetime import datetime
    >>> messages = [{'message': 'hello', 'user': 'Peter', 'datetime': datetime.now()}]
    >>> action.messages = messages

.. todo:: tutorial, starting with require_template all the way to analysis
