# -*- coding: utf-8 -*-

import pytest
from datetime import datetime, timezone

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
from pynamodb_mate.patterns.large_attribute.api import split_s3_uri, LargeAttributeMixin


class Document(pm.Model, LargeAttributeMixin):
    class Meta:
        table_name = f"pynamodb-mate-test-large-attribute-{py_ver}-{pynamodb_ver}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    pk = pm.UnicodeAttribute(hash_key=True)
    update_at = pm.UTCDateTimeAttribute()
    html = pm.UnicodeAttribute(null=True)
    image = pm.UnicodeAttribute(null=True)


prefix = f"{prefix}large_attribute/"


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class Base(BaseTest):
    @classmethod
    def setup_class_post_hook(cls):
        # clean up the table connection cache so that pynamodb can find the right boto3 session
        Document._connection = None

        if cls.use_mock:
            Document.create_table(wait=False)
            s3_client = cls.bsm.s3_client
        else:
            bsm = BotoSesManager(profile_name=aws_profile)
            s3_client = bsm.s3_client
            cls.bsm = bsm
            with bsm.awscli():
                Document.create_table(wait=True)
                Document.delete_all()
        cls.s3_client = s3_client
        try:
            s3_client.head_bucket(Bucket=bucket)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                s3_client.create_bucket(Bucket=bucket)
            else:
                raise e

    def test(self):
        # ----------------------------------------------------------------------
        # Create
        # ----------------------------------------------------------------------
        pk = "id-1"
        html_data = "<b>Hello Alice</b>".encode("utf-8")
        image_data = "this is image one".encode("utf-8")
        utc_now = get_utc_now()
        put_s3_res = Document.put_s3(
            self.bsm.s3_client,
            pk=pk,
            sk=None,
            kvs=dict(html=html_data, image=image_data),
            bucket=bucket,
            prefix=prefix,
            update_at=utc_now,
        )
        try:
            doc = Document(
                pk=pk,
                update_at=utc_now,
                **put_s3_res.to_attributes(),
            )
            doc.save()
        except Exception as e:
            put_s3_res.clean_up_when_create_dynamodb_item_failed(self.s3_client)

        # ----------------------------------------------------------------------
        # Update
        # ----------------------------------------------------------------------
        html_data = "<b>Hello Bob</b>".encode("utf-8")
        image_data = "this is image two".encode("utf-8")
        old_doc = Document.get(pk)
        utc_now = get_utc_now()
        put_s3_res = Document.put_s3(
            self.s3_client,
            pk=pk,
            sk=None,
            kvs=dict(html=html_data, image=image_data),
            bucket=bucket,
            prefix=prefix,
            update_at=utc_now,
        )
        try:
            actions = [
                getattr(Document, action.attr).set(action.s3_uri)
                for action in put_s3_res.actions
            ]
            old_doc.update(actions=actions)
            put_s3_res.clean_up_when_update_dynamodb_item_succeeded(
                self.s3_client, old_doc
            )
        except Exception as e:
            put_s3_res.clean_up_when_update_dynamodb_item_failed(
                self.s3_client, old_doc
            )

        # ----------------------------------------------------------------------
        # Delete
        # ----------------------------------------------------------------------
        doc = Document.get(pk)
        doc.delete()

        for s3_uri in [doc.html, doc.image]:
            if s3_uri:
                bucket, key = split_s3_uri(s3_uri)
                self.s3_client.delete_object(Bucket=bucket, Key=key)


class TestLargeAttributeUseMock(Base):
    use_mock = True


# @pytest.mark.skipif(is_ci, reason="Skip test that requires AWS resources in CI.")
# class TestLargeAttributeUseAws(Base):
#     use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.large_attribute", preview=False)
