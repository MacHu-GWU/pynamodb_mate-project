# -*- coding: utf-8 -*-

import typing as T
import pytest

import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import PY_VER, PYNAMODB_VER, IS_CI
from pynamodb_mate.tests.base_test import BaseTest


class YoutubeChannelIndex(pm.GlobalSecondaryIndex):
    class Meta:
        index_name = "youtube-channel-index"
        projection = pm.KeysOnlyProjection()

    channel_id: T.Union[str, pm.UnicodeAttribute] = pm.UnicodeAttribute(hash_key=True)
    video_id: T.Union[str, pm.UnicodeAttribute] = pm.UnicodeAttribute(range_key=True)


class YoutubeVideo(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-youtube-video-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    video_id: pm.REQUIRED_STR = pm.UnicodeAttribute(hash_key=True)
    channel_id: pm.OPTIONAL_STR = pm.UnicodeAttribute(default=None)

    channel_index = YoutubeChannelIndex()


class Base(BaseTest):
    model_list = [
        YoutubeVideo,
    ]

    def test(self):
        YoutubeVideo.create_table(wait=True)

        YoutubeVideo.delete_all()
        with YoutubeVideo.batch_write() as batch:
            video_id = 0
            for channel_id in range(1, 1 + 2):
                for _ in range(1, 1 + 3):
                    video_id += 1
                    video = YoutubeVideo(
                        video_id=f"video-{video_id}",
                        channel_id=f"channel-{channel_id}",
                    )
                    batch.save(video)

        result = YoutubeVideo.iter_query_index(YoutubeVideo.channel_index, "channel-1")
        assert result.one().channel_id == "channel-1"

        result = YoutubeVideo.iter_scan_index(
            YoutubeVideo.channel_index,
            filter_condition=YoutubeVideo.channel_id == "channel-1",
        )
        assert result.many(3)[0].channel_id == "channel-1"


class TestIndexUseMock(Base):
    use_mock = True


@pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
class TestIndexUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.models", preview=False)
