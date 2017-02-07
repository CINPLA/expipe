Welcome to Expipe's documentation!
==========================================

Expipe is a python module for neuroscientific data analysis.

.. toctree::
   :maxdepth: 2
   :hidden:
   
   installation
   developers_guide
   authors
   expipe
   
.. testsetup:
   
   import expipe
   expipe.ensure_testing()
   
Getting started
---------------

To get started with Expipe, a Firebase_ database needs to be set up.
Furhter, a shared storage space should be configured and mounted on all
computers using Expipe.
However, while debugging, a local folder can be used for storage.

.. _Firebase: https://firebase.google.com

After setting up a Firebase database, expipe needs to be configured.
This is done by importing expipe and running `expipe.configure`.
If you are an expipe user, please see the website of your lab for instructions
on how to run this command.
If you are involved in CINPLA, please see the 
`CINPLA setup page <https://github.com/CINPLA/expipe/wiki/CINPLA_setup>`_.

    >>> import expipe
    >>> expipe.configure( # doctest: +SKIP
    ...     data_path="",
    ...     email="",
    ...     password="",
    ...     url_prefix="",
    ...     api_key=""
    ... )
    
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
    
Modules
-------

Actions have multiple properties such as the type,
location, users and subjects.
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
    
We recommend using `expipe-browser` to edit module values.
To retrieve the values of a module, use `module.to_dict()`:

.. doctest::

    >>> print(tracking.to_dict())
    None

.. todo:: Add contents to this module
.. todo:: Documentation for retreiving values on a module.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



.. _Neo: http://packages.python.org/neo/
