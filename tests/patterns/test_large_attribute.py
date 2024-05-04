# -*- coding: utf-8 -*-

from datetime import datetime, timezone

import boto3

import pynamodb_mate as pm
from pynamodb_mate.tests import py_ver, BaseTest
from pynamodb_mate.patterns.large_attribute.api import split_s3_uri, LargeAttributeMixin


class Document(pm.Model, LargeAttributeMixin):
    class Meta:
        table_name = f"pynamodb-mate-test-large-attribute-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    pk = pm.UnicodeAttribute(hash_key=True)
    update_at = pm.UTCDateTimeAttribute()
    html = pm.UnicodeAttribute(null=True)
    image = pm.UnicodeAttribute(null=True)


BUCKET = "my-bucket"
PREFIX = "pynamodb_mate/test/patterns/large-attribute"


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class TestLargeAttribute(BaseTest):
    def setup_class(cls):
        print("")
        cls.mock_start()
        Document.create_table(wait=True)
        cls.s3_client = boto3.client("s3")
        cls.s3_client.create_bucket(Bucket=BUCKET)

    def test(self):
        # ----------------------------------------------------------------------
        # Create
        # ----------------------------------------------------------------------
        pk = "id-1"
        html_data = "<b>Hello Alice</b>".encode("utf-8")
        image_data = "this is image one".encode("utf-8")
        utc_now = get_utc_now()
        put_s3_res = Document.put_s3(
            self.s3_client,
            pk=pk,
            sk=None,
            kvs=dict(html=html_data, image=image_data),
            bucket=BUCKET,
            prefix=PREFIX,
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
            bucket=BUCKET,
            prefix=PREFIX,
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


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.large_attribute", preview=False)
