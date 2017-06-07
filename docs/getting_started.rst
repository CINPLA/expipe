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

.. testsetup::

    >>> import expipe
    >>> expipe.ensure_testing()
    >>> try:
    ...     expipe.delete_project('test', remove_all_childs=True)
    ... except NameError:
    ...     pass
    >>> try:
    ...     expipe.delete_template('hardware_daq')
    ... except NameError:
    ...     pass

Configuration
-------------

You can either configure exipe by::

    import expipe
    expipe.configure( # doctest: +SKIP
       data_path="",
       email="",
       password="",
       url_prefix="",
       api_key=""
    )

If you install the `expipe-cli` package you can configure expipe using the
command line::

    $ expipe configure --data-path /path/to/data --email my@email.com ...

For more advanced users you can add the following ``config.yaml`` file to ``~/.config/expipe``::

  .. code-block:: yaml

  data_path: c:/users/username/expipe_temp_storage
  processing:
    data_path: /home/user/expipe_temp_storage
    username: processing server username
    hostname: user@ipaddress
  storage:
    data_path: path to storage
    username: storage username
    hostname: hostname to storage
  firebase:
    email: your@email.com
    password: yourpassword
    config:
      apiKey: your-firebase-apiKey
      authDomain: your-firebase-site.firebaseapp.com
      databaseURL: https://your-firebase-site.firebaseio.com
      storageBucket: your-firebase-site.appspot.com


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

    >>> import expipe
    >>> project = expipe.require_project("test")

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

To upload a template you can write it in ``json`` or as a ``dict`` and use
``require_template``.

.. doctest::

  >>> daq_contents = {
  ...    "channel_count": {
  ...         "definition": "The number of input channels of the DAQ-device.",
  ...         "value": "64"}}
  >>> expipe.require_template(template='hardware_daq',
  ...                         contents=daq_contents)

Contents can also be a ``.json`` file::

  expipe.require_template(template='hardware_daq',
                          contents='daq_contents.json')

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

You may also view the module as ``.json`` by using the command ``to_json``:

.. doctest::

  >>> daq.to_json()
  Saving module "hardware_daq" to "hardware_daq.json"

To furter change its values and upload them to Firebase:

.. doctest::

  >>> daq_dict['gain'] = {'value': 20}
  >>> daq = action.require_module(name='hardware_daq', contents=daq_dict,
  ...                             overwrite=True)

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
