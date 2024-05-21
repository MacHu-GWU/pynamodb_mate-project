# -*- coding: utf-8 -*-

import typing as T
import pytest

from pynamodb_mate.tests.constants import IS_CI
from pynamodb_mate.tests.base_test import BaseTest
from pynamodb_mate.tests.youtube import (
    Entity,
    User,
    Video,
    Channel,
    Playlist,
    VideoOwnership,
    ChannelOwnership,
    PlaylistOwnership,
    VideoChannelAssociation,
    VideoPlaylistAssociation,
    ViewerSubscribeYoutuber,
    ViewerSubscribeChannel,
    r_setting as rs,
)


def assert_pk(lst, pks: T.List[str]):
    """
    A helper function to verify a list of items' partition key.
    """
    assert set(x.pk_id for x in lst) == set(pks)


def assert_sk(lst, sks: T.List[str]):
    """
    A helper function to verify a list of items' sort key. Usually used
    for lookup in many to many relationship.
    """
    assert set(x.sk_id for x in lst) == set(sks)


class Base(BaseTest):
    model_list = [
        Entity,
        User,
        Video,
        Channel,
        Playlist,
        VideoOwnership,
        ChannelOwnership,
        PlaylistOwnership,
        VideoChannelAssociation,
        VideoPlaylistAssociation,
        ViewerSubscribeYoutuber,
        ViewerSubscribeChannel,
    ]

    def setup_data(self):
        rs.delete_all()
        self.u_alice = rs.new_user(id="u-1", name="Alice")
        self.u_bob = rs.new_user(id="u-2", name="Bob")
        self.u_cathy = rs.new_user(id="u-3", name="Cathy")
        self.u_david = rs.new_user(id="u-4", name="David")

        self.v_alice_1 = rs.new_video(id="v-1-1", name="Alice's Video 1")
        rs.set_video_owner(conn=self.conn, video_id="v-1-1", user_id="u-1")
        self.v_alice_2 = rs.new_video(id="v-1-2", name="Alice's Video 2")
        rs.set_video_owner(conn=self.conn, video_id="v-1-2", user_id="u-1")

        self.v_bob_1 = rs.new_video(id="v-2-1", name="Bob's Video 1")
        rs.set_video_owner(conn=self.conn, video_id="v-2-1", user_id="u-2")
        self.v_bob_2 = rs.new_video(id="v-2-2", name="Bob's Video 2")
        rs.set_video_owner(conn=self.conn, video_id="v-2-2", user_id="u-2")
        self.v_bob_3 = rs.new_video(id="v-2-3", name="Bob's Video 3")
        rs.set_video_owner(conn=self.conn, video_id="v-2-3", user_id="u-2")
        self.v_bob_4 = rs.new_video(id="v-2-4", name="Bob's Video 4")
        rs.set_video_owner(conn=self.conn, video_id="v-2-4", user_id="u-2")

        self.c_alice_1 = rs.new_channel(id="c-1-1", name="Alice's Channel 1")
        rs.set_channel_owner(conn=self.conn, channel_id="c-1-1", user_id="u-1")

        self.c_bob_1 = rs.new_channel(id="c-2-1", name="Bob's Channel 1")
        rs.set_channel_owner(conn=self.conn, channel_id="c-2-1", user_id="u-2")
        self.c_bob_2 = rs.new_channel(id="c-2-2", name="Bob's Channel 2")
        rs.set_channel_owner(conn=self.conn, channel_id="c-2-2", user_id="u-2")

        self.p_cathy_1 = rs.new_playlist(id="p-3-1", name="Cathy's Playlist 1")
        rs.set_playlist_owner(conn=self.conn, playlist_id="p-3-1", user_id="u-3")
        self.p_cathy_2 = rs.new_playlist(id="p-3-2", name="Cathy's Playlist 2")
        rs.set_playlist_owner(conn=self.conn, playlist_id="p-3-2", user_id="u-3")

        rs.add_video_to_channel(video_id="v-2-1", channel_id="c-2-1")
        rs.add_video_to_channel(video_id="v-2-2", channel_id="c-2-1")
        rs.add_video_to_channel(video_id="v-2-3", channel_id="c-2-1")

        rs.add_video_to_channel(video_id="v-2-2", channel_id="c-2-2")
        rs.add_video_to_channel(video_id="v-2-3", channel_id="c-2-2")
        rs.add_video_to_channel(video_id="v-2-4", channel_id="c-2-2")

        rs.add_video_to_playlist(video_id="v-2-1", playlist_id="p-3-1")
        rs.add_video_to_playlist(video_id="v-2-2", playlist_id="p-3-1")
        rs.add_video_to_playlist(video_id="v-2-3", playlist_id="p-3-1")

        rs.add_video_to_playlist(video_id="v-2-2", playlist_id="p-3-2")
        rs.add_video_to_playlist(video_id="v-2-3", playlist_id="p-3-2")
        rs.add_video_to_playlist(video_id="v-2-4", playlist_id="p-3-2")

        rs.viewer_subscribe_youtuber(viewer_id="u-2", youtuber_id="u-1")
        rs.viewer_subscribe_youtuber(viewer_id="u-3", youtuber_id="u-1")
        rs.viewer_subscribe_youtuber(viewer_id="u-4", youtuber_id="u-1")
        rs.viewer_subscribe_youtuber(viewer_id="u-1", youtuber_id="u-2")
        rs.viewer_subscribe_youtuber(viewer_id="u-3", youtuber_id="u-2")
        rs.viewer_subscribe_youtuber(viewer_id="u-4", youtuber_id="u-3")

        rs.viewer_subscribe_channel(viewer_id="u-1", channel_id="c-2-1")
        rs.viewer_subscribe_channel(viewer_id="u-1", channel_id="c-2-2")
        rs.viewer_subscribe_channel(viewer_id="u-2", channel_id="c-1-1")
        rs.viewer_subscribe_channel(viewer_id="u-3", channel_id="c-1-1")
        rs.viewer_subscribe_channel(viewer_id="u-3", channel_id="c-2-1")
        rs.viewer_subscribe_channel(viewer_id="u-4", channel_id="c-2-2")

    # fmt: off
    def test_query(self):
        self.setup_data()

        assert_pk(rs.list_users(), ["u-1", "u-2", "u-3", "u-4"])
        assert_pk(rs.list_videos(), ["v-1-1", "v-1-2", "v-2-1", "v-2-2", "v-2-3", "v-2-4"])
        assert_pk(rs.list_channels(), ["c-1-1", "c-2-1", "c-2-2"])
        assert_pk(rs.list_playlists(), ["p-3-1", "p-3-2"])

        assert_pk(rs.find_videos_created_by_a_user("u-1"), ["v-1-1", "v-1-2"])
        assert_pk(rs.find_videos_created_by_a_user("u-2"), ["v-2-1", "v-2-2", "v-2-3", "v-2-4"])
        assert_pk(rs.find_videos_created_by_a_user("u-3"), [])
        assert_pk(rs.find_videos_created_by_a_user("u-4"), [])

        assert_pk(rs.find_channels_created_by_a_user("u-1"), ["c-1-1"])
        assert_pk(rs.find_channels_created_by_a_user("u-2"), ["c-2-1", "c-2-2"])
        assert_pk(rs.find_channels_created_by_a_user("u-3"), [])
        assert_pk(rs.find_channels_created_by_a_user("u-4"), [])

        assert_pk(rs.find_playlists_created_by_a_user("u-1"), [])
        assert_pk(rs.find_playlists_created_by_a_user("u-2"), [])
        assert_pk(rs.find_playlists_created_by_a_user("u-3"), ["p-3-1", "p-3-2"])
        assert_pk(rs.find_playlists_created_by_a_user("u-4"), [])

        assert_pk(rs.find_videos_in_channel("c-2-1"), ["v-2-1", "v-2-2", "v-2-3"])
        assert_pk(rs.find_videos_in_channel("c-2-2"), ["v-2-2", "v-2-3", "v-2-4"])

        assert_pk(rs.find_videos_in_playlist("p-3-1"), ["v-2-1", "v-2-2", "v-2-3"])
        assert_pk(rs.find_videos_in_playlist("p-3-2"), ["v-2-2", "v-2-3", "v-2-4"])

        assert_pk(rs.find_subscribers_for_youtuber("u-1"), ["u-2", "u-3", "u-4"])
        assert_pk(rs.find_subscribers_for_youtuber("u-2"), ["u-1", "u-3"])
        assert_pk(rs.find_subscribers_for_youtuber("u-3"), ["u-4"])
        assert_pk(rs.find_subscribers_for_youtuber("u-4"), [])

        assert_sk(rs.find_subscribed_youtubers("u-1"), ["u-2"])
        assert_sk(rs.find_subscribed_youtubers("u-2"), ["u-1"])
        assert_sk(rs.find_subscribed_youtubers("u-3"), ["u-1", "u-2"])
        assert_sk(rs.find_subscribed_youtubers("u-4"), ["u-1", "u-3"])

        assert_pk(rs.find_subscribers_for_channel("c-1-1"), ["u-2", "u-3"])
        assert_pk(rs.find_subscribers_for_channel("c-2-1"), ["u-1", "u-3"])
        assert_pk(rs.find_subscribers_for_channel("c-2-2"), ["u-1", "u-4"])

        assert_sk(rs.find_subscribed_channels("u-1"), ["c-2-1", "c-2-2"])
        assert_sk(rs.find_subscribed_channels("u-2"), ["c-1-1"])
        assert_sk(rs.find_subscribed_channels("u-3"), ["c-1-1", "c-2-1"])
        assert_sk(rs.find_subscribed_channels("u-4"), ["c-2-2"])

    def test_unset_one_to_many(self):
        self.setup_data()

        # we only do transaction write but not transaction read
        # we cannot read immediately after write,
        # that's we need to final all write operations first
        # then exam the result.
        rs.unsubscribe_all_youtuber(viewer_id="u-1")
        rs.unsubscribe_all_channel(viewer_id="u-1")
        rs.clear_playlist(playlist_id="p-3-1")
        rs.clear_channel(channel_id="c-2-1")

        assert_pk(rs.find_subscribers_for_youtuber("u-2"), ["u-3"])
        assert_sk(rs.find_subscribed_youtubers("u-1"), [])

        assert_pk(rs.find_subscribers_for_channel("c-2-1"), ["u-3"])
        assert_pk(rs.find_subscribers_for_channel("c-2-2"), ["u-4"])
        assert_sk(rs.find_subscribed_channels("u-1"), [])

        assert_pk(rs.find_videos_in_playlist("p-3-1"), [])

        assert_pk(rs.find_videos_in_channel("c-2-1"), [])
    # fmt: on


class TestRelationshipUseMock(Base):
    use_mock = True


@pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
class TestRelationshipUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.relationship", preview=False)
