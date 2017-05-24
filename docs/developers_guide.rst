=================
Developers' guide
=================


Getting the source code
-----------------------

We use the Git version control system. The best way to contribute is through
GitHub_. You will first need a GitHub account, and you should then fork the
repository.

Working on the documentation
----------------------------

The documentation is written in reStructuredText, using the Sphinx
documentation system. To build the documentation::

    $ cd expipe/docs
    $ make html

Then open `doc/build/html/index.html` in your browser.

Committing your changes
-----------------------

Once you are happy with your changes, **run the test suite again to check
that you have not introduced any new bugs**. Then you can commit them to your
local repository::

    $ git commit -m 'informative commit message'

If this is your first commit to the project, please add your name and
affiliation/employer to :file:`doc/source/authors.rst`

You can then push your changes to your online repository on GitHub::

    $ git push

Once you think your changes are ready to be included in the main Neo repository,
open a pull request on GitHub (see https://help.github.com/articles/using-pull-requests).

Testing
-------

**WARNING**: Tests can be destructive and have to be run on a different server.
Use `expipe-debug.firebaseio.com` for testing.

A separate config file needs to be created if you want to run tests. The config
file needs to be placed in `~/.config/expipe/test-config.yaml` and must have
the key `allow_tests: true`. Here is an example:

.. code-block:: yaml

  allow_tests: true
  data_path: '/tmp/expipe-data'
  firebase:
    email: <needs to be changed>
    password: <needs to be changed>
    config:
      apiKey: AIzaSyBnbsraKxrO8zv1qVZeAvJR4fEWzExQhOM
      authDomain: expipe-debug.firebaseapp.com
      databaseURL: https://expipe-debug.firebaseio.com
      storageBucket: expipe-debug.appspot.com

.. _GitHub: http://github.com
