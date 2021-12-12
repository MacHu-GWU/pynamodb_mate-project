.. image:: https://readthedocs.org/projects/pynamodb_mate/badge/?version=latest
    :target: https://pynamodb_mate.readthedocs.io/
    :alt: Documentation Status

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

- `Full Documentation is Here <https://pynamodb_mate.readthedocs.io/>`_

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


Overview
------------------------------------------------------------------------------

``pynamodb_mate`` provides advanced best practice using DynamoDB in python. Built on top of `pynamodb <https://pynamodb.readthedocs.io/en/latest/>`_ python library. It maintain the compatibility to major version of ``pynamodb`` library. For example ``pynamodb_mate>=5.0.0,<6.0.0`` is compatible to ``pynamodb>=5.0.0,<6.0.0``.


Feature1. Store Large Object in Dynamodb
------------------------------------------------------------------------------
DynamoDB is a very good choice for **Pay-as-you-go**, **high-concurrent** key value database. Sometimes, you want to store large binary object as a Dynamodb item attribute. For example, a web crawler app wants to store crawled html source to avoid re-visit the same url. But Dynamodb has a limitation that one item can not be larger than 256KB. How could you solve the problem?

A easy solution is to store large binary object in s3, and only store the s3 uri in Dynamodb. ``pynamodb_mate`` library provides this feature on top of ``pynamodb`` project (A DynamoDB ORM layer in Python).

**1. Define your Data Model**

.. code-block:: python

    import pynamodb_mate
    import botocore.session

    # Declare the data Model

    # create s3 client, will be used to store big binary / text data in S3
    boto_ses = botocore.session.get_session()
    s3_client = boto_ses.create_client("s3")

    class UrlModel(pynamodb_mate.Model):
        class Meta:
            table_name = "urls"
            region = "us-east-1"
            # use Pay as you go model for testing
            billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

        url = pynamodb_mate.UnicodeAttribute(hash_key=True)

        html = pynamodb_mate.S3BackedBigTextAttribute()
        html.bucket_name = "my-bucket"  # s3 bucket name
        html.s3_client = s3_client  # s3 client object

        content = pynamodb_mate.S3BackedBigBinaryAttribute()
        content.bucket_name = "my-bucket"
        content.s3_client = s3_client

    # create dynamodb table if not exists, quick skip if already exists
    UrlModel.create_table(wait=True)

**2. Write / Read / Update / Delete**

.. code-block:: python

    url = "https://pynamodb-mate.readthedocs.io/en/latest/"
    html = "<html>Hello World!</html>\n" * 1000
    content = ("this is a dummy image!\n" * 1000).encode("utf-8")

    # create item
    url = UrlModel(url=url, html=html, content=content)

    # write item to dynamodb table
    url.save()

    # get the item
    url = UrlModel.get(url)
    assert url.html == html
    assert url.content == content

    # update the item
    url.update(
        actions=[
            UrlModel.html.set("<html>Hello Dynamodb</html>"),
            UrlModel.content.set("this is a real image!".encode("utf-8")),
        ]
    )
    url.refresh() # get the up-to-date data
    print(url.html) # should give you new data
    print(url.content) # should give you new data

    # delete item from dynamodb, DON'T DELETE S3 OBJECT
    url.delete()

**3. How it Works**

In this example, you can pass the raw html to ``url = UrlModel(html="<html>big HTML ...</html>", ...)`` attribute. When writing this item to Dynamodb, it automatically use the sha256 fingerprint of the data in S3 key naming convention, stores the S3 uri to the ``html`` field, and store the html content to S3 object. In other words, same data will be stored at the same S3 location to avoid duplicate traffic. However, it won't delete the S3 object because there might be another item are using the same S3 object.


Feature2. Client Side Encryption
------------------------------------------------------------------------------
Dynamodb support encryption at the rest (Server Side Encryption) and use SSL to encryption the transit data (Encrypt at the fly) by default. But you need to spend additional work to enable "Client Side Encryption". ``pynamodb_mate`` made it deadly easy.

**1. Define attribute to use Client Side Encryption (AES)**

.. code-block:: python

    import pynamodb_mate

    ENCRYPTION_KEY = "my-password"

    class ArchiveModel(pynamodb_mate.Model):
        class Meta:
            table_name = f"archive"
            region = "us-east-1"
            billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

        aid = pynamodb_mate.UnicodeAttribute(hash_key=True)

        secret_message = pynamodb_mate.EncryptUnicodeAttribute()
        # the per field level encryption key
        secret_message.encryption_key = ENCRYPTION_KEY
        # if True, same input -> same output
        # so you can still use this field for query
        # ``filter_conditions=(ArchiveModel.secret_message == "my message")``
        secret_message.determinative = True

        secret_binary = pynamodb_mate.EncryptBinaryAttribute()
        secret_binary.encryption_key = ENCRYPTION_KEY
        # if True, same input -> random output, but will return same output
        # but you lose the capability of query on this field
        secret_binary.determinative = False

        secret_integer = pynamodb_mate.EncryptedNumberAttribute()
        secret_integer.encryption_key = ENCRYPTION_KEY
        secret_integer.determinative = True

        secret_float = pynamodb_mate.EncryptedNumberAttribute()
        secret_float.encryption_key = ENCRYPTION_KEY
        secret_float.determinative = False

        secret_data = pynamodb_mate.EncryptedJsonAttribute()
        secret_data.encryption_key = ENCRYPTION_KEY
        secret_data.determinative = False

    # create dynamodb table if not exists, quick skip if already exists
    ArchiveModel.create_table(wait=True)

**2. Write / Read the Item**

.. code-block:: python

    msg = "attack at 2PM tomorrow!"
    binary = "a secret image".encode("utf-8")
    data = {"Alice": 1, "Bob": 2, "Cathy": 3}

    model = ArchiveModel(
        aid="aid-001",
        secret_message=msg,
        secret_binary=binary,
        secret_integer=1234,
        secret_float=3.14,
        secret_data=data,
    )
    model.save()

    model = ArchiveModel.get("aid-001")
    assert model.secret_message == msg
    assert model.secret_binary == binary
    assert model.secret_integer == 1234
    assert model.secret_float == pytest.approx(3.14)
    assert model.secret_data == data

**3. How it works**

Internally it always use binary for data serialization / deserialization. It convert the original data to binary, encrypt it with the key, and store it to DynamoDB. It read the data from DynamoDB, decrypt it and convert it back to original data to user.

For field that you still want to be able to query on it, you use ``determinative = True``. And it uses AES ECB. It is approved that not secure for middle man attack. But you can still use it with DynamoDB because DynamoDB api use SSL to encrypt it in transit. For ``determinative = False``, it uses AES CTR.


Feature3. Compressed Attribute
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
    # Save item to Dynamodb
    order.save()

    # Get the value back and verify
    order = OrderModel.get(order_id)
    assert order.description == description
    assert order.image == image
    assert order.items == items

**3. How it works**

Internally it always use binary for data serialization / deserialization. It convert the original data to binary, and compress it before saving to Dynamodb. It read the data from DynamoDB, decompress it and convert it back to original data to user.


.. _install:

Install
------------------------------------------------------------------------------

``pynamodb_mate`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install pynamodb_mate

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade pynamodb_mate
