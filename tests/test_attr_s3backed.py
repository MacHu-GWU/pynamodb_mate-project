# -*- coding: utf-8 -*-

import botocore.session
import pynamodb_mate
from pynamodb_mate.tests import py_ver, BUCKET_NAME
from pynamodb_mate.helpers import remove_s3_prefix


boto_ses = botocore.session.get_session()
s3_client = boto_ses.create_client("s3")

prefix = "projects/pynamodb_mate/unit-test/s3backed/"


class UrlModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-url-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    url = pynamodb_mate.UnicodeAttribute(hash_key=True)

    html = pynamodb_mate.S3BackedBigTextAttribute()
    html.bucket_name = BUCKET_NAME
    html.key_template = f"{prefix}/{{fingerprint}}.txt"
    html.s3_client = s3_client

    content = pynamodb_mate.S3BackedBigBinaryAttribute()
    content.bucket_name = BUCKET_NAME
    content.key_template = f"{prefix}/{{fingerprint}}.dat"
    content.s3_client = s3_client


def setup_module(module):
    UrlModel.create_table(wait=True)
    remove_s3_prefix(s3_client, BUCKET_NAME, prefix)


url = "www.python.org"
html = "<b>Hello World</b>" * 1000
content = html.encode("utf-8")


def test_io():
    model = UrlModel(
        url=url,
        html=html,
        content=content,
    )
    model.save()

    model = UrlModel.get(url)
    assert model.html == html
    assert model.content == content

    new_html = "<b>Hello Python</b>" * 1000
    new_content = new_html.encode("utf-8")

    model.update(
        actions=[
            UrlModel.html.set(new_html),
            UrlModel.content.set(new_content),
        ]
    )
    model.refresh()
    assert model.html == new_html
    assert model.content == new_content


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.s3backed")
