Feature 1. Store Large Object in DynamoDB
------------------------------------------------------------------------------
DynamoDB is a very good choice for **Pay-as-you-go**, **high-concurrent** key value database. Sometimes, you want to store large binary object as a DynamoDB item attribute. For example, a web crawler app wants to store crawled html source to avoid re-visit the same url. But DynamoDB has a limitation that one item can not be larger than 256KB. How could you solve the problem?

A easy solution is to store large binary object in s3, and only store the s3 uri in DynamoDB. ``pynamodb_mate`` library provides this feature on top of ``pynamodb`` project (A DynamoDB ORM layer in Python).

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

    # create DynamoDB table if not exists, quick skip if already exists
    UrlModel.create_table(wait=True)

**2. Write / Read / Update / Delete**

.. code-block:: python

    url = "https://pynamodb-mate.readthedocs.io/en/latest/"
    html = "<html>Hello World!</html>\n" * 1000
    content = ("this is a dummy image!\n" * 1000).encode("utf-8")

    # create item
    url = UrlModel(url=url, html=html, content=content)

    # write item to DynamoDB table
    url.save()

    # get the item
    url = UrlModel.get(url)
    assert url.html == html
    assert url.content == content

    # update the item
    url.update(
        actions=[
            UrlModel.html.set("<html>Hello DynamoDB</html>"),
            UrlModel.content.set("this is a real image!".encode("utf-8")),
        ]
    )
    url.refresh() # get the up-to-date data
    print(url.html) # should give you new data
    print(url.content) # should give you new data

    # delete item from DynamoDB, DON'T DELETE S3 OBJECT
    url.delete()

**3. How it Works**

In this example, you can pass the raw html to ``url = UrlModel(html="<html>big HTML ...</html>", ...)`` attribute. When writing this item to DynamoDB, it automatically use the sha256 fingerprint of the data in S3 key naming convention, stores the S3 uri to the ``html`` field, and store the html content to S3 object. In other words, same data will be stored at the same S3 location to avoid duplicate traffic. However, it won't delete the S3 object because there might be another item are using the same S3 object.