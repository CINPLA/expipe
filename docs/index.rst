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

.. doctest::

    >>> import expipe
    >>> expipe.configure(
    ...     data_path="",
    ...     email="",
    ...     password="",
    ...     url_prefix="",
    ...     api_key=""
    ... )
    


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



.. _Neo: http://packages.python.org/neo/
