# -*- coding: utf-8 -*-

"""
验证 hash key 和 range key 支不支持 update 操作的.

结论: **不支持**
"""

import pynamodb_mate
from pynamodb_mate.tests import py_ver


class CommentModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-forum-comment-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    post_id = pynamodb_mate.UnicodeAttribute(hash_key=True)
    comment_nth = pynamodb_mate.NumberAttribute(range_key=True)


CommentModel.create_table(wait=True)
comment = CommentModel(post_id="p001", comment_nth=1)
comment.save()
comment.update(actions=[CommentModel.post_id.set("p002")])
comment.update(actions=[CommentModel.comment_nth.set(2)])
