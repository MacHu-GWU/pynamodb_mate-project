# -*- coding: utf-8 -*-

import os

import boto3
import pynamodb.models

import pynamodb_mate
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb_mate.attributes.bigbinaryattribute import (
    BigBinaryAttribute, BigTextAttribute,
)

# from pynamodb_mate import all
s3_client = boto3.client("s3")
bucket_name = "aws-data-lab-sanhe-for-everything"


class Url(Model):
    class Meta:
        table_name = "pynamodb-mate-dev-url"
        billing_mode = pynamodb.models.PAY_PER_REQUEST_BILLING_MODE

    url = UnicodeAttribute(hash_key=True)
    content = BigBinaryAttribute(
        bucket_name=bucket_name, s3_client=s3_client,
    )
    # html = BigTextAttribute(
    #     bucket_name=bucket_name, s3_client=s3_client,
    # )

print(dir(Url.content))
print(Url.content._is_protocol)
Url.create_table(wait=True)

# url = Url(
#     url="www.python.org",
#     content="hello python".encode("utf-8"),
#     # html="hello python",
# )
# url.save()
#
# url = Url.get("www.python.org")
# print([
#     url.content,
#     # url.html,
# ])

# url.update(
#     actions=[
#         Url.content.set("hello ruby".encode("utf-8"))
#     ]
# )

# url = Url.get("www.python.org")
# print(url.content)
