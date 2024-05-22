# -*- coding: utf-8 -*-

import pytest
from datetime import datetime, timezone

from s3pathlib import S3Path
import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import (
    PY_VER,
    PYNAMODB_VER,
    IS_CI,
    BUCKET,
    PREFIX,
)
from pynamodb_mate.tests.base_test import BaseTest
from pynamodb_mate.patterns.large_attribute.api import (
    get_s3_key,
    split_s3_uri,
    LargeAttributeMixin,
)
from rich import print as rprint


class Document(pm.Model, LargeAttributeMixin):
    class Meta:
        table_name = f"pynamodb-mate-test-large-attribute-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    pk = pm.UnicodeAttribute(hash_key=True)
    update_at = pm.UTCDateTimeAttribute()
    html = pm.UnicodeAttribute(null=True)
    image = pm.UnicodeAttribute(null=True)
    data = pm.DynamicMapAttribute()


PREFIX = f"{PREFIX}large_attribute/"


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class UserError(Exception):
    pass


class Base(BaseTest):
    model_list = [
        Document,
    ]

    # def test(self):
    #     # ----------------------------------------------------------------------
    #     # Create
    #     # ----------------------------------------------------------------------
    #     pk = "id-1"
    #     html_data = "<b>Hello Alice</b>".encode("utf-8")
    #     image_data = "this is image one".encode("utf-8")
    #     utc_now = get_utc_now()
    #     put_s3_res = Document.put_s3(
    #         self.bsm.s3_client,
    #         pk=pk,
    #         sk=None,
    #         kvs=dict(html=html_data, image=image_data),
    #         bucket=BUCKET,
    #         prefix=PREFIX,
    #         update_at=utc_now,
    #     )
    #     # try:
    #     doc = Document(
    #         pk=pk,
    #         update_at=utc_now,
    #         data={"version": 1},
    #         **put_s3_res.to_attributes(),
    #     )
    #     doc.save()
    #     # except Exception as e:
    #     #     print(e)
    #     #     put_s3_res.clean_up_when_create_dynamodb_item_failed(self.s3_client)
    #
    #     # ----------------------------------------------------------------------
    #     # Update
    #     # ----------------------------------------------------------------------
    #     html_data = "<b>Hello Bob</b>".encode("utf-8")
    #     image_data = "this is image two".encode("utf-8")
    #     old_doc = Document.get(pk)
    #     utc_now = get_utc_now()
    #     put_s3_res = Document.put_s3(
    #         self.s3_client,
    #         pk=pk,
    #         sk=None,
    #         kvs=dict(html=html_data, image=image_data),
    #         bucket=BUCKET,
    #         prefix=PREFIX,
    #         update_at=utc_now,
    #     )
    #     try:
    #         actions = [
    #             getattr(Document, action.attr).set(action.s3_uri)
    #             for action in put_s3_res.actions
    #         ]
    #         old_doc.update(actions=actions)
    #         put_s3_res.clean_up_when_update_dynamodb_item_succeeded(
    #             self.s3_client, old_doc
    #         )
    #     except Exception as e:
    #         put_s3_res.clean_up_when_update_dynamodb_item_failed(
    #             self.s3_client, old_doc
    #         )
    #
    #     # ----------------------------------------------------------------------
    #     # Delete
    #     # ----------------------------------------------------------------------
    #     doc = Document.get(pk)
    #     doc.delete()
    #
    #     for s3_uri in [doc.html, doc.image]:
    #         if s3_uri:
    #             bucket, key = split_s3_uri(s3_uri)
    #             self.s3_client.delete_object(Bucket=bucket, Key=key)

    def test_transaction(self):
        # ----------------------------------------------------------------------
        # Create
        # ----------------------------------------------------------------------
        pk = "id-1"
        sk = None
        html_data = "<b>Hello Alice</b>".encode("utf-8")
        image_data = "this is image one".encode("utf-8")
        utc_now = get_utc_now()

        with pytest.raises(UserError):
            doc = Document.create_large_attribute_item(
                s3_client=self.bsm.s3_client,
                pk=pk,
                sk=sk,
                kvs=dict(html=html_data, image=image_data),
                bucket=BUCKET,
                prefix=PREFIX,
                update_at=utc_now,
                attributes=dict(update_at=utc_now, data={"version": 1}),
                clean_up_when_failed=True,
                _error=UserError(),
            )

        # DynamoDB write operation should be failed
        assert Document.get_one_or_none(pk, sk) is None
        # S3 object should be cleaned up
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.html.attr_name,
            value=html_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").exists(bsm=self.bsm) is False
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.image.attr_name,
            value=image_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").exists(bsm=self.bsm) is False

        doc = Document.create_large_attribute_item(
            s3_client=self.bsm.s3_client,
            pk=pk,
            sk=sk,
            kvs=dict(html=html_data, image=image_data),
            bucket=BUCKET,
            prefix=PREFIX,
            update_at=utc_now,
            attributes=dict(update_at=utc_now, data={"version": 1}),
            clean_up_when_failed=True,
        )

        # DynamoDB write operation should be succeeded
        doc = Document.get_one_or_none(pk, sk)
        assert doc.data["version"] == 1
        # S3 object should be created
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.html.attr_name,
            value=html_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").read_bytes(bsm=self.bsm) == html_data
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.image.attr_name,
            value=image_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").read_bytes(bsm=self.bsm) == image_data

        # ----------------------------------------------------------------------
        # Update
        # ----------------------------------------------------------------------
        # --- failed
        html_data = "<b>Hello Bob</b>".encode("utf-8")
        image_data = "this is image two".encode("utf-8")
        old_doc = Document.get(pk)
        utc_now = get_utc_now()

        with pytest.raises(UserError):
            new_doc = Document.update_large_attribute_item(
                s3_client=self.bsm.s3_client,
                pk=pk,
                sk=sk,
                kvs=dict(html=html_data, image=image_data),
                bucket=BUCKET,
                prefix=PREFIX,
                update_at=utc_now,
                update_actions=[
                    Document.update_at.set(utc_now),
                    Document.data.set({"version": 2}),
                ],
                clean_up_when_succeeded=True,
                clean_up_when_failed=True,
                _error=UserError(),
            )

        # DynamoDB update operation should be failed
        doc = Document.get_one_or_none(pk, sk)
        assert doc.update_at == old_doc.update_at
        assert doc.html == old_doc.html
        assert doc.image == old_doc.image
        assert doc.data["version"] == 1

        # S3 object of old document should still be there
        assert S3Path(old_doc.html).exists(bsm=self.bsm) is True
        assert S3Path(old_doc.image).exists(bsm=self.bsm) is True
        # S3 object of new document should be cleaned up
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.html.attr_name,
            value=html_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").exists(bsm=self.bsm) is False
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.image.attr_name,
            value=image_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").exists(bsm=self.bsm) is False

        # --- succeeded
        new_doc = Document.update_large_attribute_item(
            s3_client=self.bsm.s3_client,
            pk=pk,
            sk=sk,
            kvs=dict(html=html_data, image=image_data),
            bucket=BUCKET,
            prefix=PREFIX,
            update_at=utc_now,
            update_actions=[
                Document.update_at.set(utc_now),
                Document.data.set({"version": 2}),
            ],
            clean_up_when_succeeded=True,
            clean_up_when_failed=True,
        )

        # DynamoDB update operation should be succeeded
        doc = Document.get_one_or_none(pk, sk)
        assert new_doc.serialize() == doc.serialize()
        assert doc.update_at > old_doc.update_at
        assert doc.html != old_doc.html
        assert doc.image != old_doc.image
        assert doc.data["version"] == 2

        # S3 object of old document should be cleaned up
        assert S3Path(old_doc.html).exists(bsm=self.bsm) is False
        assert S3Path(old_doc.image).exists(bsm=self.bsm) is False

        # S3 object of new document should be created
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.html.attr_name,
            value=html_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").read_bytes(bsm=self.bsm) == html_data
        key = get_s3_key(
            pk=pk,
            sk=sk,
            attr=Document.image.attr_name,
            value=image_data,
            prefix=PREFIX,
        )
        assert S3Path(f"s3://{BUCKET}/{key}").read_bytes(bsm=self.bsm) == image_data

        # ----------------------------------------------------------------------
        # Delete
        # ----------------------------------------------------------------------
        old_doc = Document.get(pk)
        Document.delete_large_attribute_item(
            s3_client=self.bsm.s3_client,
            pk=pk,
            sk=sk,
            attributes=[
                Document.html.attr_name,
                Document.image.attr_name,
            ],
            clean_up_when_succeeded=True,
        )

        # DynamoDB delete operation should be succeeded
        assert Document.get_one_or_none(pk, sk) is None

        # S3 object of old document should be cleaned up
        assert S3Path(old_doc.html).exists(bsm=self.bsm) is False
        assert S3Path(old_doc.image).exists(bsm=self.bsm) is False


class TestLargeAttributeUseMock(Base):
    use_mock = True


# @pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
# class TestLargeAttributeUseAws(Base):
#     use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.large_attribute", preview=False)
