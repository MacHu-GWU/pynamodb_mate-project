# -*- coding: utf-8 -*-

import pytest
import time

import botocore.exceptions
from boto_session_manager import BotoSesManager
import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import (
    py_ver,
    pynamodb_ver,
    aws_profile,
    is_ci,
    bucket,
    prefix,
)
from pynamodb_mate.tests.base_test import BaseTest


prefix = f"{prefix}s3backed/"


class UrlModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-url-{py_ver}-{pynamodb_ver}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    url = pm.UnicodeAttribute(hash_key=True)

    html = pm.attributes.S3BackedBigTextAttribute(
        bucket_name=bucket,
        key_template=f"{prefix}{{fingerprint}}.html",
        s3_client=None,
    )

    content = pm.attributes.S3BackedBigBinaryAttribute(
        bucket_name=bucket,
        key_template=f"{prefix}{{fingerprint}}.dat",
        s3_client=None,
    )

    data = pm.attributes.S3BackedJsonDictAttribute(
        bucket_name=bucket,
        key_template=f"{prefix}{{fingerprint}}.json",
        compressed=False,
        s3_client=None,
    )


class Base(BaseTest):
    @classmethod
    def setup_class_post_hook(cls):
        # clean up the table connection cache so that pynamodb can find the right boto3 session
        UrlModel._connection = None

        if cls.use_mock:
            UrlModel.create_table(wait=False)
            s3_client = cls.bsm.s3_client
        else:
            bsm = BotoSesManager(profile_name=aws_profile)
            s3_client = bsm.s3_client
            with bsm.awscli():
                UrlModel.create_table(wait=True)
                UrlModel.delete_all()

        UrlModel.html.s3_client = s3_client
        UrlModel.content.s3_client = s3_client
        UrlModel.data.s3_client = s3_client

        try:
            s3_client.head_bucket(Bucket=bucket)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                s3_client.create_bucket(Bucket=bucket)
            else:
                raise e

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
            pm.attributes.S3BackedBigTextAttribute(
                bucket_name=bucket,
                key_template=f"invalid_template",
                s3_client=self.bsm.s3_client,
            )


class TestS3BackedAttributeUseMock(Base):
    use_mock = True


@pytest.mark.skipif(is_ci, reason="Skip test that requires AWS resources in CI.")
class TestS3BackedAttributeUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.s3backed", preview=False)
