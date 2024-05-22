# -*- coding: utf-8 -*-

"""
验证 hash key 和 range key 支不支持 update 操作.

结论: **不支持**
"""

import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import PY_VER, PYNAMODB_VER


class CommentModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-forum-comment-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    post_id: pm.REQUIRED_STR = pm.UnicodeAttribute(hash_key=True)
    comment_nth: pm.REQUIRED_INT = pm.NumberAttribute(range_key=True)


CommentModel.create_table(wait=True)
comment = CommentModel(post_id="p001", comment_nth=1)
comment.save()
comment.update(actions=[CommentModel.post_id.set("p002")])
comment.update(actions=[CommentModel.comment_nth.set(2)])
