Introduction
------------

We are witnessing a revolution in methodology in neuroscience today,
due to technological advances. The vast collection of recording setups used on a
variety of experimental subjects puts high demands on flexible data organization.

To ease this organization we introduce a tool for the experiment pipeline named
`expipe`. The aims of `expipe` is to organize metadata in a way such that they:

* are flexible towards a multitude of user aspects.
* are readable for humans and machines for many years to come.
* are sharable.
* support high throughput data analysis.
* support multiple types of large-scale data sets.

To this end we use the flexible `Firebase <https://firebase.google.com/>`_
NoSQL type database to store metadata. This way of storing metadata consist of
assigning key value pairs in a `json <http://www.json.org/>`_ type format.

During an experiment metadata can be automatically added by user specific
`templates`. Templates are prefilled key value pairs describing all aspects
of your experiments e.g. recording environment, acquisition system etc.
When added, `templates` are introduced as `modules` which are descriptors of
`project` and/or `action` entities. A `project` is the
root object during communication with `expipe` and contain `modules` and `actions`.
Actions are individual, well actions, of interaction with experimental assets
or `expipe` itself such as recordings or analysis respectively. Actions also contain
`modules` which are specific to a particular `action` in contrast to `project`
`modules` which are more general.

We encourage users from neuroscience to base templates on the
`odML terminologies <http://www.g-node.org/projects/odml/terminologies>`_ which
can be `a priori` filled out by a user or added in an empty state for
`a posteriori` documentation.

There exist other projects of similar goals (see e.g.
`Alyx <http://alyx.readthedocs.io/en/latest/>`_,
`LabLog <http://lablog.sourceforge.net/>`_)
