.. Astrocyte Packager documentation master file.

Welcome to Astrocyte Packager's documentation!
==============================================

.. image:: https://github.com/dbbs-lab/astrocyte/workflows/Unit%20tests/badge.svg
    :target: https://github.com/dbbs-lab/astrocyte

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: https://readthedocs.org/projects/astrocyte/badge/?version=latest
   :target: https://astrocyte.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Installation
------------

::

   pip install astrocyte


Usage
-----

::

   astro create package my-package


Fill in the prompts and navigate to your package folder.

::

   astro add mod /path/to/mod/file

After adding any amount of mod files to your package you can build it and upload or
install it::

   astro build
   astro install
   astro upload

For use on your local computer either use::

   astro add mod --local /path/to/mod/file

This installs it to a local package that is immediately available.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
