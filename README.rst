.. image:: https://readthedocs.org/projects/pynamodb_mate/badge/?version=latest
    :target: https://pynamodb_mate.readthedocs.io/index.html
    :alt: Documentation Status

.. image:: https://travis-ci.org/MacHu-GWU/pynamodb_mate-project.svg?branch=master
    :target: https://travis-ci.org/MacHu-GWU/pynamodb_mate-project?branch=master

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
      :target: https://pynamodb_mate.readthedocs.io/index.html

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


Feature1. Store Large Binary Object in S3, only store S3 URI in DynamoDB
------------------------------------------------------------------------------

DynamoDB is a very good choice for **Pay-as-you-go**, **high-concurrent** key value database. Somestimes, you want to store large binary object along with Dynamodb items. Especially, in web crawler app. But Dynamodb has a limitation that one item can not be larger than 250KB. How could you solve the problem?

A easy solution is to store large binary object in s3, and only store the s3 uri in Dynamodb. ``pynamodb_mate`` library provides this feature on top of ``pynamodb`` project (A DynamoDB ORM layer in Python).

Here's how you define your ORM layer:

.. code-block:: python

    from pynamodb.models import Model
    from pynamodb.attributes import UnicodeAttribute
    from pynamodb_mate.s3_backed_attribute import (
        S3BackedBinaryAttribute,
        S3BackedUnicodeAttribute,
        S3BackedMixin,
        s3_key_safe_b64encode,
    )

    BUCKET_NAME = "my-bucket"
    URI_PREFIX = "s3://{BUCKET_NAME}/".format(BUCKET_NAME=BUCKET_NAME)

    class PageModel(Model, S3BackedMixin):
        class Meta:
            table_name = "pynamodb_mate-pages"
            region = "us-east-1"

        url = UnicodeAttribute(hash_key=True)
        cover_image_url = UnicodeAttribute(null=True)

        # this field is for html content string
        html_content = S3BackedUnicodeAttribute(
            s3_uri_getter=lambda obj: URI_PREFIX + s3_key_safe_b64encode(obj.url) + ".html",
            compress=True,
        )
        # this field is for image binary content
        cover_image_content = S3BackedBinaryAttribute(
            s3_uri_getter=lambda obj: URI_PREFIX + s3_key_safe_b64encode(obj.cover_image_url) + ".jpg",
            compress=True,
        )

Here's how you store large binary to s3:

.. code-block:: python

    url = "http://www.python.org"
    url_cover_image = "http://www.python.org/logo.jpg"

    html_content = "Hello World!\n" * 1000
    cover_image_content = ("this is a dummy image!\n" * 1000).encode("utf-8")

    page = PageModel(url=url, cover_image_url=url_cover_image)

    # create, if something wrong with s3.put_object in the middle,
    # dirty s3 object will be cleaned up
    page.atomic_save(
        s3_backed_data=[
            page.html_content.set_to(html_content),
            page.cover_image_content.set_to(cover_image_content)
        ]
    )

    # update, if something wrong with s3.put_object in the middle,
    # partially done new s3 object will be roll back
    html_content_new = "Good Bye!\n" * 1000
    cover_image_content_new = ("this is another dummy image!\n" * 1000).encode("utf-8")

    page.atomic_update(
        s3_backed_data=[
            page.html_content.set_to(html_content_new),
            page.cover_image_content.set_to(cover_image_content_new),
        ]
    )

    # delete, make sure s3 object are all gone
    page.atomic_delete()


.. _install:

Install
------------------------------------------------------------------------------

``pynamodb_mate`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install pynamodb_mate

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade pynamodb_mate
