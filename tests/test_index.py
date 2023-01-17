# -*- coding: utf-8 -*-

import typing as T

import pynamodb_mate as pm
from pynamodb_mate.tests import py_ver, BaseTest


class YoutubeChannelIndex(pm.GlobalSecondaryIndex):
    class Meta:
        index_name = "youtube-channel-index"
        projection = pm.KeysOnlyProjection()

    channel_id: T.Union[str, pm.UnicodeAttribute] = pm.UnicodeAttribute(hash_key=True)
    video_id: T.Union[str, pm.UnicodeAttribute] = pm.UnicodeAttribute(range_key=True)


class YoutubeVideo(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-youtube-video-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    video_id: T.Union[str, pm.UnicodeAttribute] = pm.UnicodeAttribute(hash_key=True)
    channel_id: T.Optional[T.Union[str, pm.UnicodeAttribute]] = pm.UnicodeAttribute(
        default=None
    )

    channel_index = YoutubeChannelIndex()


class TestModel(BaseTest):
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


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.models", preview=False)
