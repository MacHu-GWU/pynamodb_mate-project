# -*- coding: utf-8 -*-

import os
import pytest
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb_mate.s3_backed_attribute import (
    S3BackedBinaryAttribute,
    S3BackedUnicodeAttribute,
    S3BackedMixin,
    s3_key_safe_b64encode,
)

AWS_PROFILE = "pynamodb_mate"
os.environ["AWS_DEFAULT_PROFILE"] = AWS_PROFILE

BUCKET_NAME = "pyrabbit"
KEY_PREFIX = "pypi-test/pynamodb_mate/"
URI_PREFIX = "s3://{BUCKET_NAME}/{KEY_PREFIX}".format(
    BUCKET_NAME=BUCKET_NAME, KEY_PREFIX=KEY_PREFIX)


class PageModel(Model, S3BackedMixin):
    class Meta:
        table_name = "pynamodb_mate-pages"
        region = "us-east-1"

    url = UnicodeAttribute(hash_key=True)
    cover_image_url = UnicodeAttribute(null=True)

    html_content = S3BackedUnicodeAttribute(
        s3_uri_getter=lambda obj: URI_PREFIX +
        s3_key_safe_b64encode(obj.url) + ".html",
        compress=True,
    )
    cover_image_content = S3BackedBinaryAttribute(
        s3_uri_getter=lambda obj: URI_PREFIX +
        s3_key_safe_b64encode(obj.cover_image_url) + ".jpg",
        compress=True,
    )


def setup_module(object):
    PageModel.create_table(read_capacity_units=5, write_capacity_units=5)


class TestS3BackedMixin(object):
    def test_get_s3_backed_attr_mapper(self):
        assert "html_content" in PageModel.get_s3_backed_attr_mapper()
        assert "cover_image_content" in PageModel.get_s3_backed_attr_mapper()

        assert PageModel.html_content.name == "html_content"
        assert PageModel.cover_image_content.name == "cover_image_content"

    def test(self):
        url = "http://www.python.org"
        url_cover_image = "http://www.python.org/logo.jpg"

        html_content = "Hello World!\n" * 1000
        cover_image_content = (
            "this is a dummy image!\n" * 1000).encode("utf-8")

        # create
        page = PageModel(url=url, cover_image_url=url_cover_image)

        # save binary to s3
        page.atomic_save(
            s3_backed_data=[
                page.html_content.set_to(html_content),
                page.cover_image_content.set_to(cover_image_content)
            ]
        )
        assert page.html_content.read_data(page) == html_content
        assert page.cover_image_content.read_data(page) == cover_image_content

        # update
        html_content_new = "Good Bye!\n" * 1000
        cover_image_content_new = (
            "this is another dummy image!\n" * 1000).encode("utf-8")

        page.atomic_update(
            s3_backed_data=[
                page.html_content.set_to(html_content_new),
                page.cover_image_content.set_to(cover_image_content_new),
            ]
        )
        assert page.html_content.read_data(page) == html_content_new
        assert page.cover_image_content.read_data(
            page) == cover_image_content_new

        # delete binary on s3
        page.atomic_delete()
        with pytest.raises(Exception):
            page.html_content.read_data(page)
        with pytest.raises(Exception):
            page.cover_image_content.read_data(page)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
