.. image:: https://readthedocs.org/projects/pynamodb_mate/badge/?version=latest
    :target: https://pynamodb_mate.readthedocs.io/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/pynamodb_mate-project/workflows/CI/badge.svg
    :target: https://github.com/MacHu-GWU/pynamodb_mate-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/pynamodb_mate-project/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/pynamodb_mate-project

.. image:: https://img.shields.io/pypi/v/pynamodb_mate.svg
    :target: https://pypi.python.org/pypi/pynamodb_mate

.. image:: https://img.shields.io/pypi/l/pynamodb_mate.svg
    :target: https://pypi.python.org/pypi/pynamodb_mate

.. image:: https://img.shields.io/pypi/pyversions/pynamodb_mate.svg
    :target: https://pypi.python.org/pypi/pynamodb_mate

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/pynamodb_mate-project

------

.. image:: https://img.shields.io/badge/Link-Document-blue.svg
      :target: https://pynamodb_mate.readthedocs.io/

.. image:: https://img.shields.io/badge/Link-API-blue.svg
      :target: https://pynamodb_mate.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
      :target: https://pynamodb_mate.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
      :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
      :target: https://github.com/MacHu-GWU/pynamodb_mate-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
      :target: https://github.com/MacHu-GWU/pynamodb_mate-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
      :target: https://github.com/MacHu-GWU/pynamodb_mate-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
      :target: https://pypi.org/pypi/pynamodb_mate#files


Welcome to ``pynamodb_mate`` Documentation
==============================================================================
📙 `Full Documentation is Here <https://pynamodb_mate.readthedocs.io/>`_

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


Overview
------------------------------------------------------------------------------
``pynamodb_mate`` provides advanced best practice using DynamoDB in python. Built on top of `pynamodb <https://pynamodb.readthedocs.io/en/latest/>`_ python library. It maintain the compatibility to major version of ``pynamodb`` library. For example ``pynamodb_mate>=5.0.0,<6.0.0`` is compatible to ``pynamodb>=5.0.0,<6.0.0``.


Disclaimer
------------------------------------------------------------------------------
Even though the author is a Dynamodb Subject Matter Expert from AWS, but this project is NOT an AWS official project, and it is a personal open source project for the Python community.


Features
------------------------------------------------------------------------------
Click on the link below to see detailed tutorial and examples.

- ⭐ `Store Large Object in DynamoDB <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/Store-Large-Object-in-DynamoDB.ipynb>`_: This feature allows you to store any Python object and arbitrary big data in DynamoDB that can exceed the 400KB limit.
- ⭐ `Client Side Encryption <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/Client-Side-Encryption.ipynb>`_: This feature allows you to use your own encryption key to encrypt your data before it is sent to the DynamoDB.
- ⭐ `Compressed Attribute <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/Compressed-Attribute.ipynb>`_: This feature can automatically compress the data before it is sent to the DynamoDB.
- ⭐ `AWS DynamoDB Console Url <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/AWS-DynamoDB-Console-Url.ipynb>`_: This feature can print the AWS DynamoDB console url for the table, items. You can use this in you log to quickly jump to the console to debug.


DynamoDB Patterns
------------------------------------------------------------------------------
``pynamodb_mate`` also provides some commonly used patterns. It is based on the author's experience providing solutions to many customers from different industries. Click on the link below to see detailed tutorial and examples.

- 🎉 `Cache <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/patterns/cache.ipynb>`_: This feature gives you a "Redis" liked, serverless, Zero-ops, auto-scaling, high performance, pay-as-you-go cache layer based on DynamoDB.
- 🎉 `Status Tracker <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/patterns/status-tracker.ipynb>`_: This feature gives you the ability to track status of each task, and error-handling, retry, concurrency control out-of-the-box.


.. _install:

Install
------------------------------------------------------------------------------
``pynamodb_mate`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install pynamodb_mate

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade pynamodb_mate

In order to use the following feature, you need to run ``pip install pynamodb_mate[encrypt]`` first:

- ``pynamodb_mate.EncryptedNumberAttribute``
- ``pynamodb_mate.EncryptedUnicodeAttribute``
- ``pynamodb_mate.EncryptedBinaryAttribute``
- ``pynamodb_mate.EncryptedJsonDictAttribute``
