.. image:: https://readthedocs.org/projects/pynamodb_mate/badge/?version=latest
    :target: https://pynamodb-mate.readthedocs.io/
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

.. image:: https://img.shields.io/pypi/dm/pynamodb-mate.svg
    :target: https://pypi.python.org/pypi/pynamodb_mate

.. image:: https://img.shields.io/badge/Release_History!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/release-history.rst

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/pynamodb_mate-project

------

.. image:: https://img.shields.io/badge/Link-Document-blue.svg
      :target: https://pynamodb-mate.readthedocs.io/

.. image:: https://img.shields.io/badge/Link-API-blue.svg
      :target: https://pynamodb-mate.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
      :target: https://pynamodb-mate.readthedocs.io/py-modindex.html

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
📙 `Full Documentation is Here <https://pynamodb-mate.readthedocs.io/>`_

.. image:: https://pynamodb-mate.readthedocs.io/en/latest/_static/pynamodb_mate-logo.png
    :target: https://pynamodb-mate.readthedocs.io/


Overview
------------------------------------------------------------------------------
``pynamodb_mate`` provides advanced best practice using DynamoDB in python. Built on top of `pynamodb <https://pynamodb.readthedocs.io/en/latest/>`_ python library. It maintain the compatibility to major version of ``pynamodb`` library. For example ``pynamodb_mate>=5.0.0,<6.0.0`` is compatible to ``pynamodb>=5.0.0,<6.0.0``, ``pynamodb_mate==5.5.1.X`` is compatible to ``pynamodb>=5.5.1,<6.0.0``, ``pynamodb_mate==6.0.0.X`` is compatible to ``pynamodb>=6.0.0,<7.0.0``.


Disclaimer
------------------------------------------------------------------------------
Even though the author is a Dynamodb Subject Matter Expert from AWS, but this project is NOT an AWS official project, and it is a personal open source project for the Python community.


Features
------------------------------------------------------------------------------
``pynamodb_mate`` provides some commonly used patterns. It is based on the author's experience providing solutions to many customers from different industries. Click on the link below to see detailed tutorial and examples.

- ⭐ `Store Large Object in DynamoDB <https://pynamodb-mate.readthedocs.io/en/latest/01-Store-Large-Object-in-DynamoDB/index.html>`_: This feature allows you to store any Python object and arbitrary big data in DynamoDB that can exceed the 400KB limit. It also handles data consistency and data integrity between DynamoDB and S3.
- ⭐ `Client Side Encryption <https://pynamodb-mate.readthedocs.io/en/latest/02-Client-Side-Encryption/index.html>`_: This feature allows you to use your own encryption key to encrypt your data before it is sent to the DynamoDB.
- ⭐ `Compressed Attribute <https://pynamodb-mate.readthedocs.io/en/latest/03-Compressed-Attribute/index.html>`_: This feature can automatically compress the data before it is sent to the DynamoDB, it would save you a lot of money if you use JSON attribute in DynamoDB.
- ⭐ `AWS DynamoDB Console Url <https://pynamodb-mate.readthedocs.io/en/latest/04-DynamoDB-Consule-Url/index.html>`_: This feature can print the AWS DynamoDB console url for the table, items. You can use this in you log to quickly jump to the console to debug.
- ⭐ `Use DynamoDB as a Cache Backend <https://pynamodb-mate.readthedocs.io/en/latest/05-Use-DynamoDB-as-Cache-Backend/index.html>`_: This feature gives you a "Redis" liked, serverless, Zero-ops, auto-scaling, high performance, pay-as-you-go cache layer based on DynamoDB.
- ⭐ `Enable status tracking for business critical application using Amazon DynamoDB <https://pynamodb-mate.readthedocs.io/en/latest/06-Status-Tracker/index.html>`_: This feature gives you the ability to track status of each task, and error-handling, retry, concurrency control out-of-the-box.
- ⭐ `Modeling Relational Data in DynamoDB <https://pynamodb-mate.readthedocs.io/en/latest/07-Modeling-Relational-Data-in-DynamoDB/index.html>`_: This feature allow you to manage mass amount entity and one-to-many, many-to-many relationship in DynamoDB using the ultimate data modeling strategy that has high performance and scales well. Made data modeling in DynamoDB deadly simple.


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
