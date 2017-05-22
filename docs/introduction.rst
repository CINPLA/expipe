Introduction
------------

In neuroscience today, due to technological advances, we are witnessing a
revolution in methodology. The vast collection of recording setups used on a
variety of experimental subjects puts high demands on flexible data organization.

We introduce an organization tool named `expipe` which aims to organize
metadata in a way such that they are:

* support flexible metadata.
* readable for humans and machines for many years to come.
* sharable.
* support high throughput data analysis.
* support multiple types of large-scale data sets.

To this end we use the flexible `Firebase <https://firebase.google.com/>`_
NoSQL type database to store metadata.
This way of storing metadata consist of assigning key value
pairs in a `json <http://www.json.org/>`_ type format. Metadata is automatically
added specified by the user through templates. Templates are then loaded as
modules which are descriptors of project or action entities. A project is the
root object during communication with expipe and contain modules and actions.
Actions are individual, well actions, of interaction with experimental assets
or expipe such recordings or analysis respectively. Actions also contain
modules which are specific to this particular action in contrast to project
modules which are more general.

We encourage users from neuroscience to base templates on the
`odML terminologies <http://www.g-node.org/projects/odml/terminologies>`_ which
can be `a priori` filled out by a user or added in an empty state for
`a posteriori` documentation.

There exist other projects of similar goals (see
`Alyx <http://alyx.readthedocs.io/en/latest/>`_,
`LabLog <http://lablog.sourceforge.net/>`_)
