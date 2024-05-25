# -*- coding: utf-8 -*-

import typing as T
import base64
from datetime import datetime, timezone

import moto
import requests
from boto_session_manager import BotoSesManager
from s3pathlib import S3Path, context
import pynamodb_mate.api as pm
from rich import print as rprint

st = pm.patterns.status_tracker
la = pm.patterns.large_attribute

mock_s3 = moto.mock_s3()
mock_dynamodb = moto.mock_dynamodb()
mock_sts = moto.mock_sts()

mock_s3.start()
mock_dynamodb.start()
mock_sts.start()

bsm = BotoSesManager()
context.attach_boto_session(bsm.boto_ses)
print(f"{bsm.aws_account_id = }")
conn = pm.Connection()


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def b64encode_url(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")


def b64decode_url(b64: str) -> str:
    return base64.urlsafe_b64decode(b64.encode("utf-8")).decode("utf-8")


class StatusEnum(st.BaseStatusEnum):
    pending = 10
    in_progress = 20
    failed = 30
    succeeded = 40
    ignored = 50


class Task(
    st.BaseTask,
    pm.patterns.large_attribute.LargeAttributeMixin,
):
    class Meta:
        table_name = "crawler_tasks"
        region = bsm.aws_region
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    html: pm.OPTIONAL_STR = pm.UnicodeAttribute(null=True)

    status_and_update_time_index = st.StatusAndUpdateTimeIndex()

    config = st.TrackerConfig.make(
        use_case_id="crawler",
        pending_status=StatusEnum.pending.value,
        in_progress_status=StatusEnum.in_progress.value,
        failed_status=StatusEnum.failed.value,
        succeeded_status=StatusEnum.succeeded.value,
        ignored_status=StatusEnum.ignored.value,
        n_pending_shard=1,
        n_in_progress_shard=1,
        n_failed_shard=1,
        n_succeeded_shard=1,
        n_ignored_shard=1,
        status_zero_pad=3,
        status_shard_zero_pad=3,
        max_retry=3,
        lock_expire_seconds=15,  # 抓取一个网页最多耗时 5-10 秒
    )

    @property
    def url(self):
        return b64decode_url(self.task_id)


Task.create_table(wait=True)
url = "https://www.python.org/"
task_id = b64encode_url(url)
task = Task.make_and_save(task_id=task_id)


s3dir_root = S3Path(f"s3://my-bucket/{Task.config.use_case_id}/html/").to_dir()
bsm.s3_client.create_bucket(Bucket=s3dir_root.bucket)


class CrawlError(Exception):
    pass


exec_ctx: st.ExecutionContext
with Task.start(task_id=task_id, detailed_error=True, debug=True) as exec_ctx:
    task: Task = exec_ctx.task
    res = requests.get(task.url)
    if res.status_code != 200:
        raise CrawlError(f"Failed to download {url}")
    html = res.text
    utc_now = get_utc_now()
    Task.update_large_attribute_item(
        s3_client=bsm.s3_client,
        pk=task.key,
        sk=None,
        kvs=dict(html=html.encode("utf-8")),
        bucket=s3dir_root.bucket,
        prefix=s3dir_root.key,
        update_at=utc_now,
        clean_up_when_succeeded=True,
        clean_up_when_failed=True,
    )

task = Task.get_one_or_none(task_id=task_id)

print("----- HTML ----")
print(S3Path(task.html).read_text())
print("----- DynamoDB Item ----")
rprint(task.to_simple_dict())

mock_s3.stop()
mock_dynamodb.stop()
mock_sts.stop()