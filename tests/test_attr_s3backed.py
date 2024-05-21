# -*- coding: utf-8 -*-

import pytest
import time

from boto_session_manager import BotoSesManager
from pynamodb.connection import Connection
import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import (
    PY_VER,
    PYNAMODB_VER,
    IS_CI,
    AWS_PROFILE,
    BUCKET,
    PREFIX,
)
from pynamodb_mate.tests.base_test import BaseTest


prefix = f"{PREFIX}s3backed/"


class UrlModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-url-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    url = pm.UnicodeAttribute(hash_key=True)

    html = pm.attributes.S3BackedBigTextAttribute(
        bucket_name=BUCKET,
        key_template=f"{prefix}{{fingerprint}}.html",
        s3_client=None,
    )

    content = pm.attributes.S3BackedBigBinaryAttribute(
        bucket_name=BUCKET,
        key_template=f"{prefix}{{fingerprint}}.dat",
        s3_client=None,
    )

    data = pm.attributes.S3BackedJsonDictAttribute(
        bucket_name=BUCKET,
        key_template=f"{prefix}{{fingerprint}}.json",
        compressed=False,
        s3_client=None,
    )


class Base(BaseTest):
    model_list = [
        UrlModel,
    ]

    @classmethod
    def setup_class(cls):
        cls.setup_class_pre_hook()
        cls.setup_moto()

        # code below is for making sure pynamodb connection can find the right boto3 session
        # to use in mock mode or AWS mode. The pynamodb connection design is flawed,
        # we have to do some hacky things to make it work.
        for model_class in cls.model_list:
            cls.cleanup_connection(model_class)
            model_class.Meta.region = cls.region_name
        if cls.use_mock:
            cls.s3_client = cls.bsm.s3_client
            cls.create_bucket(cls.s3_client, BUCKET)
            UrlModel.html.s3_client = cls.s3_client
            UrlModel.content.s3_client = cls.s3_client
            UrlModel.data.s3_client = cls.s3_client
            cls.conn = Connection()
            for model_class in cls.model_list:
                model_class.create_table(wait=False)
        else:
            # create s3 bucket first, sometimes Model.delete_all() will fail if the bucket not exists
            cls.bsm = BotoSesManager(profile_name=AWS_PROFILE)
            with cls.bsm.awscli():
                cls.s3_client = cls.bsm.s3_client
                cls.create_bucket(cls.s3_client, BUCKET)
                UrlModel.html.s3_client = cls.s3_client
                UrlModel.content.s3_client = cls.s3_client
                UrlModel.data.s3_client = cls.s3_client
                cls.conn = Connection()
                _ = cls.conn.session.get_credentials()
                for model_class in cls.model_list:
                    model_class.create_table(wait=True)
                    model_class.delete_all()
        cls.setup_class_post_hook()

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
                bucket_name=BUCKET,
                key_template=f"invalid_template",
                s3_client=self.bsm.s3_client,
            )


class TestS3BackedAttributeUseMock(Base):
    use_mock = True


# @pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
# class TestS3BackedAttributeUseAws(Base):
#     use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.s3backed", preview=False)
