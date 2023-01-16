# -*- coding: utf-8 -*-

import boto3
import pytest
import time

import moto
import pynamodb_mate
from pynamodb_mate.tests import py_ver, BUCKET_NAME, BaseTest
from pynamodb_mate.helpers import remove_s3_prefix


prefix = "projects/pynamodb_mate/unit-test/s3backed/"

with moto.mock_s3():
    s3_client = boto3.client("s3")

    class UrlModel(pynamodb_mate.Model):
        class Meta:
            table_name = f"pynamodb-mate-test-url-{py_ver}"
            region = "us-east-1"
            billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

        url = pynamodb_mate.UnicodeAttribute(hash_key=True)

        html = pynamodb_mate.S3BackedBigTextAttribute(
            bucket_name=BUCKET_NAME,
            key_template=f"{prefix}{{fingerprint}}.html",
            s3_client=s3_client,
        )

        content = pynamodb_mate.S3BackedBigBinaryAttribute(
            bucket_name=BUCKET_NAME,
            key_template=f"{prefix}{{fingerprint}}.dat",
            s3_client=s3_client,
        )

        data = pynamodb_mate.S3BackedJsonDictAttribute(
            bucket_name=BUCKET_NAME,
            key_template=f"{prefix}{{fingerprint}}.json",
            compressed=False,
            s3_client=s3_client,
        )


class TestS3BackedBigTextAttribute(BaseTest):
    @classmethod
    def setup_class(cls):
        cls.mock_start()

        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        remove_s3_prefix(s3_client, BUCKET_NAME, prefix)

        UrlModel.create_table(wait=True)

    def test(self):
        url = "www.python.org"
        html = "<b>Hello World</b>" * 1
        content = html.encode("utf-8")
        data = {"a": 1, "b": 2, "c": 3}

        url_model = UrlModel(
            url=url,
            html=html,
            content=content,
            data=data,
        )
        url_model.save()

        url_model = UrlModel.get(url)
        assert url_model.html == html
        assert url_model.content == content
        assert url_model.data == data

        new_html = "<b>Hello Python</b>" * 1000
        new_content = new_html.encode("utf-8")
        new_data = {"x": 1, "y": 2, "z": 3}
        url_model.update(
            actions=[
                UrlModel.html.set(new_html),
                UrlModel.content.set(new_content),
                UrlModel.data.set(new_data),
            ]
        )
        time.sleep(1)
        url_model.refresh()
        assert url_model.html == new_html
        assert url_model.content == new_content
        assert url_model.data == new_data

    def test_exception(self):
        with pytest.raises(ValueError):
            pynamodb_mate.S3BackedBigTextAttribute(
                bucket_name=BUCKET_NAME,
                key_template=f"invalid_template",
                s3_client=s3_client,
            )


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.s3backed", preview=False)
