# -*- coding: utf-8 -*-

import typing as T
import pytest

from pynamodb_mate.tests.constants import IS_CI
from pynamodb_mate.tests.base_test import BaseTest
from pynamodb_mate.tests.youtube_v2 import (
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
    T_Entity,
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


def print_all(lst: T.Iterable[T_Entity]):
    for entity in lst:
        entity.print_vip_attrs()


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
        Entity.delete_all()

        # fmt: off
        self.u_alice = User.new_entity(id="u-1", name="Alice")
        self.u_bob = User.new_entity(id="u-2", name="Bob")
        self.u_cathy = User.new_entity(id="u-3", name="Cathy")
        self.u_david = User.new_entity(id="u-4", name="David")

        self.v_alice_1 = Video.new_entity(id="v-1-1", name="Alice's Video 1")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-1-1", one_entity_id="u-1")
        self.v_alice_2 = Video.new_entity(id="v-1-2", name="Alice's Video 2")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-1-2", one_entity_id="u-1")

        self.v_bob_1 = Video.new_entity(id="v-2-1", name="Bob's Video 1")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-2-1", one_entity_id="u-2")
        self.v_bob_2 = Video.new_entity(id="v-2-2", name="Bob's Video 2")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-2-2", one_entity_id="u-2")
        self.v_bob_3 = Video.new_entity(id="v-2-3", name="Bob's Video 3")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-2-3", one_entity_id="u-2")
        self.v_bob_4 = Video.new_entity(id="v-2-4", name="Bob's Video 4")
        VideoOwnership.set_one_to_many(conn=self.conn, many_entity_id="v-2-4", one_entity_id="u-2")

        self.c_alice_1 = Channel.new_entity(id="c-1-1", name="Alice's Channel 1")
        ChannelOwnership.set_one_to_many(conn=self.conn, many_entity_id="c-1-1", one_entity_id="u-1")

        self.c_bob_1 = Channel.new_entity(id="c-2-1", name="Bob's Channel 1")
        ChannelOwnership.set_one_to_many(conn=self.conn, many_entity_id="c-2-1", one_entity_id="u-2")
        self.c_bob_2 = Channel.new_entity(id="c-2-2", name="Bob's Channel 2")
        ChannelOwnership.set_one_to_many(conn=self.conn, many_entity_id="c-2-2", one_entity_id="u-2")

        self.p_cathy_1 = Playlist.new_entity(id="p-3-1", name="Cathy's Playlist 1")
        PlaylistOwnership.set_one_to_many(conn=self.conn, many_entity_id="p-3-1", one_entity_id="u-3")
        self.p_cathy_2 = Playlist.new_entity(id="p-3-2", name="Cathy's Playlist 2")
        PlaylistOwnership.set_one_to_many(conn=self.conn, many_entity_id="p-3-2", one_entity_id="u-3")

        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-1", right_entity_id="c-2-1")
        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-2", right_entity_id="c-2-1")
        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-3", right_entity_id="c-2-1")

        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-2", right_entity_id="c-2-2")
        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-3", right_entity_id="c-2-2")
        VideoChannelAssociation.set_many_to_many(left_entity_id="v-2-4", right_entity_id="c-2-2")

        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-1", right_entity_id="p-3-1")
        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-2", right_entity_id="p-3-1")
        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-3", right_entity_id="p-3-1")

        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-2", right_entity_id="p-3-2")
        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-3", right_entity_id="p-3-2")
        VideoPlaylistAssociation.set_many_to_many(left_entity_id="v-2-4", right_entity_id="p-3-2")

        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-2", right_entity_id="u-1")
        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-3", right_entity_id="u-1")
        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-4", right_entity_id="u-1")
        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-1", right_entity_id="u-2")
        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-3", right_entity_id="u-2")
        ViewerSubscribeYoutuber.set_many_to_many(left_entity_id="u-4", right_entity_id="u-3")

        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-1", right_entity_id="c-2-1")
        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-1", right_entity_id="c-2-2")
        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-2", right_entity_id="c-1-1")
        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-3", right_entity_id="c-1-1")
        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-3", right_entity_id="c-2-1")
        ViewerSubscribeChannel.set_many_to_many(left_entity_id="u-4", right_entity_id="c-2-2")
        # fmt: on

    # fmt: off
    def test_query(self):
        self.setup_data()

        assert User.get_entity("u-1").user_id == "u-1"
        assert Video.get_entity("v-1-1").video_id == "v-1-1"
        assert Channel.get_entity("c-1-1").channel_id == "c-1-1"
        assert Playlist.get_entity("p-3-1").playlist_id == "p-3-1"

        assert_pk(User.list_entity(), ["u-1", "u-2", "u-3", "u-4"])
        assert_pk(Video.list_entity(), ["v-1-1", "v-1-2", "v-2-1", "v-2-2", "v-2-3", "v-2-4"])
        assert_pk(Channel.list_entity(), ["c-1-1", "c-2-1", "c-2-2"])
        assert_pk(Playlist.list_entity(), ["p-3-1", "p-3-2"])

        assert_pk(VideoOwnership.find_many_by_one("u-1"), ["v-1-1", "v-1-2"])
        assert_pk(VideoOwnership.find_many_by_one("u-2"), ["v-2-1", "v-2-2", "v-2-3", "v-2-4"])
        assert_pk(VideoOwnership.find_many_by_one("u-3"), [])
        assert_pk(VideoOwnership.find_many_by_one("u-4"), [])

        assert VideoOwnership.find_one_by_many("v-1-1").sk_id == "u-1"

        assert_pk(ChannelOwnership.find_many_by_one("u-1"), ["c-1-1"])
        assert_pk(ChannelOwnership.find_many_by_one("u-2"), ["c-2-1", "c-2-2"])
        assert_pk(ChannelOwnership.find_many_by_one("u-3"), [])
        assert_pk(ChannelOwnership.find_many_by_one("u-4"), [])

        assert ChannelOwnership.find_one_by_many("c-1-1").sk_id == "u-1"

        assert_pk(PlaylistOwnership.find_many_by_one("u-1"), [])
        assert_pk(PlaylistOwnership.find_many_by_one("u-2"), [])
        assert_pk(PlaylistOwnership.find_many_by_one("u-3"), ["p-3-1", "p-3-2"])
        assert_pk(PlaylistOwnership.find_many_by_one("u-4"), [])

        assert PlaylistOwnership.find_one_by_many("p-3-1").sk_id == "u-3"

        assert_pk(VideoChannelAssociation.find_many_by_many("c-2-1", lookup_by_left=False), ["v-2-1", "v-2-2", "v-2-3"])
        assert_pk(VideoChannelAssociation.find_many_by_many("c-2-2", lookup_by_left=False), ["v-2-2", "v-2-3", "v-2-4"])

        assert_pk(VideoPlaylistAssociation.find_many_by_many("p-3-1", lookup_by_left=False), ["v-2-1", "v-2-2", "v-2-3"])
        assert_pk(VideoPlaylistAssociation.find_many_by_many("p-3-2", lookup_by_left=False), ["v-2-2", "v-2-3", "v-2-4"])

        assert_pk(ViewerSubscribeYoutuber.find_many_by_many("u-1", lookup_by_left=False), ["u-2", "u-3", "u-4"])
        assert_pk(ViewerSubscribeYoutuber.find_many_by_many("u-2", lookup_by_left=False), ["u-1", "u-3"])
        assert_pk(ViewerSubscribeYoutuber.find_many_by_many("u-3", lookup_by_left=False), ["u-4"])
        assert_pk(ViewerSubscribeYoutuber.find_many_by_many("u-4", lookup_by_left=False), [])

        assert_sk(ViewerSubscribeYoutuber.find_many_by_many("u-1", lookup_by_left=True), ["u-2"])
        assert_sk(ViewerSubscribeYoutuber.find_many_by_many("u-2", lookup_by_left=True), ["u-1"])
        assert_sk(ViewerSubscribeYoutuber.find_many_by_many("u-3", lookup_by_left=True), ["u-1", "u-2"])
        assert_sk(ViewerSubscribeYoutuber.find_many_by_many("u-4", lookup_by_left=True), ["u-1", "u-3"])

        assert_pk(ViewerSubscribeChannel.find_many_by_many("c-1-1", lookup_by_left=False), ["u-2", "u-3"])
        assert_pk(ViewerSubscribeChannel.find_many_by_many("c-2-1", lookup_by_left=False), ["u-1", "u-3"])
        assert_pk(ViewerSubscribeChannel.find_many_by_many("c-2-2", lookup_by_left=False), ["u-1", "u-4"])

        assert_sk(ViewerSubscribeChannel.find_many_by_many("u-1", lookup_by_left=True), ["c-2-1", "c-2-2"])
        assert_sk(ViewerSubscribeChannel.find_many_by_many("u-2", lookup_by_left=True), ["c-1-1"])
        assert_sk(ViewerSubscribeChannel.find_many_by_many("u-3", lookup_by_left=True), ["c-1-1", "c-2-1"])
        assert_sk(ViewerSubscribeChannel.find_many_by_many("u-4", lookup_by_left=True), ["c-2-2"])

    def test_unset_one_to_many(self):
        self.setup_data()

        # we only do transaction write but not transaction read
        # we cannot read immediately after write,
        # that's we need to final all write operations first
        # then exam the result.
        ViewerSubscribeYoutuber.clear_many_by_many("u-1", lookup_by_left=True)
        ViewerSubscribeChannel.clear_many_by_many("u-1", lookup_by_left=True)
        VideoPlaylistAssociation.clear_many_by_many("p-3-1", lookup_by_left=False)
        VideoChannelAssociation.clear_many_by_many("c-2-1", lookup_by_left=False)

        assert_pk(ViewerSubscribeYoutuber.find_many_by_many("u-2", lookup_by_left=False), ["u-3"])
        assert_sk(ViewerSubscribeYoutuber.find_many_by_many("u-1", lookup_by_left=True), [])

    #
        assert_pk(ViewerSubscribeChannel.find_many_by_many("c-2-1", lookup_by_left=False), ["u-3"])
        assert_pk(ViewerSubscribeChannel.find_many_by_many("c-2-2", lookup_by_left=False), ["u-4"])
        assert_sk(ViewerSubscribeChannel.find_many_by_many("u-1", lookup_by_left=True), [])

        assert_pk(VideoPlaylistAssociation.find_many_by_many("p-3-1", lookup_by_left=False), [])
        assert_pk(VideoChannelAssociation.find_many_by_many("c-2-1", lookup_by_left=False), [])
    # fmt: on


class TestRelationshipUseMock(Base):
    use_mock = True


# @pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
# class TestRelationshipUseAws(Base):
#     use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.relationship_v2", preview=False)
