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


Feature 3. Compressed Attribute
------------------------------------------------------------------------------
Sometimes you want to compress the data before store to save DB space. For example, in a E-commerce data model, an order has many items like this: ``[{"item_name": "apple", "item_count": 12}, {"item_name": "banana", "item_count": 5}]``. There are lots of repeated information such as the keys ``"item_name"`` and ``"item_count"``.

**1. Define attribute to use Auto Compressed**

.. code-block:: python

    import pynamodb_mate

    # Define the Data Model to use compressed attribute
    class OrderModel(pynamodb_mate.Model):
        class Meta:
            table_name = f"orders"
            region = "us-east-1"
            billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

        order_id = pynamodb_mate.UnicodeAttribute(hash_key=True)

        # original value is unicode str
        description = pynamodb_mate.CompressedUnicodeAttribute(null=True)

        # original value is binary bytes
        image = pynamodb_mate.CompressedBinaryAttribute(null=True)

        # original value is any json serializable object
        items = pynamodb_mate.CompressedJSONAttribute(null=True)

    OrderModel.create_table(wait=True)

**2. Write / Read the Item**

.. code-block:: python

    # Create an item
    order_id = "order_001"
    description = "a fancy order!" * 10
    image = description.encode("utf-8") # a fake binary object
    items = [
        {
            "item_id": "i_001",
            "item_name": "apple",
            "item_price": 2.4,
            "quantity": 8,
        },
        {
            "item_id": "i_002",
            "item_name": "banana",
            "item_price": 0.53,
            "quantity": 5,
        },
    ]
    order = OrderModel(
        order_id=order_id,
        description=description,
        image=image,
        items=items,
    )
    # Save item to DynamoDB
    order.save()

    # Get the value back and verify
    order = OrderModel.get(order_id)
    assert order.description == description
    assert order.image == image
    assert order.items == items

**3. How it works**

Internally it always use binary for data serialization / deserialization. It convert the original data to binary, and compress it before saving to DynamoDB. It read the data from DynamoDB, decompress it and convert it back to original data to user.


Feature 4. AWS DynamoDB Console
------------------------------------------------------------------------------
You can use the following methods to create a URL that can preview your table and items in your browser. This could be very helpful with logging.

.. code-block:: python


        print(Model.get_table_overview_console_url())
        print(Model.get_table_items_console_url())
        print(Model(the_hash_key="a", the_range_key=1).item_detail_console_url)


Feature 5. DynamoDB Patterns
------------------------------------------------------------------------------
``pynamodb_mate`` also provides some commonly used patterns as base ORM models. It is based on the author's working experience dealing with many customers from many kinds of industry.

Available patterns:

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`See example <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/patterns/cache.ipynb>`_

A lots of developer love Redis. However, redis is not a serverless solution, and you need to manage the server (or cluster). **DynamoDB naturally is a serverless, distributive, Key-Value database that has very high read and write throughput. It is a good choice to use DynamoDB as a cache without technique overhead**.

Benefit

- There's no server to manage.
- DynamoDB has a latency around 20ms per request.
- DynamoDB cache backend can be created in 5 seconds.
- DynamoDB has pay-as-you-go pricing model, you only pay for what you use.
- DynamoDB automatically scales up and down to adapt your traffic.
- Unlike other local cache solutions, it is on cloud and has access management out-of-the-box.


Status Tracker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`See example <https://github.com/MacHu-GWU/pynamodb_mate-project/blob/master/examples/patterns/status-tracker.ipynb>`_

It many business critical use case, it is necessary to track every task to know which is succeeded, which is failed and which is still in progress. Some advanced users also wants to:

- Each task should be handled by only one worker, you want a concurrency lock mechanism to avoid double consumption.
- For those succeeded tasks, store additional information such as the output of the task and log the success time.
- For those failed task, log the error message for debug, so you can fix the bug and rerun the task.
- For those failed task, you want to get all of failed tasks by one simple query and rerun with the updated business logic.
- For those tasks failed too many times, you don't want to retry them anymore and wants to ignore them.
- Run custom query based on task status for analytics purpose.

With DynamoDB, you can enable this advanced status tracking feature for your application with just a few lines of code. And you can use the "elegant" context manager to wrap around your business logic code and enjoy all the features above.


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
- ``pynamodb_mate.EncryptedJsonAttribute``



