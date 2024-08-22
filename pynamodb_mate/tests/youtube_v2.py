# -*- coding: utf-8 -*-

"""
https://docs.google.com/spreadsheets/d/1PG2YyBoH2NoPyhcGhweARX2XdbRlh8-EEH9YD4IidHU/edit#gid=1357852845
"""

import typing as T

import pynamodb_mate.api as pm
from pynamodb_mate.patterns.relationship_v2 import api as rl
from iterproxy import IterProxy

from .constants import PY_VER, PYNAMODB_VER


class LookupIndex(rl.BaseLookupIndex):
    class Meta:
        index_name = "lookup-index"
        projection = pm.AllProjection()


class Meta:
    table_name = f"pynamodb-mate-test-youtube-entity-{PY_VER}-{PYNAMODB_VER}"
    region = "us-east-1"
    billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE


class Entity(rl.BaseEntity):
    """
    :param pk: partition key can only has alpha letter and hyphen.
    """

    Meta = Meta

    lookup_index = LookupIndex()

    def print_vip_attrs(self):
        print(self.get_vip_attrs())


class User(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.EntityType(name="User")

    @property
    def user_id(self) -> str:
        return self.pk_id


class Video(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.EntityType(name="Video")

    @property
    def video_id(self) -> str:
        return self.pk_id


class Channel(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.EntityType(name="Channel")

    @property
    def channel_id(self) -> str:
        return self.pk_id


class Playlist(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.EntityType(name="Playlist")

    @property
    def playlist_id(self) -> str:
        return self.pk_id


class VideoOwnership(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.OneToManyRelationshipType(
        name="Video-Ownership",
        one_type=User,
        many_type=Video,
    )

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class ChannelOwnership(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.OneToManyRelationshipType(
        name="Channel-Ownership",
        one_type=User,
        many_type=Channel,
    )

    @property
    def channel_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class PlaylistOwnership(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.OneToManyRelationshipType(
        name="Playlist-Ownership",
        one_type=User,
        many_type=Playlist,
    )

    @property
    def playlist_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class VideoChannelAssociation(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.ManyToManyRelationshipType(
        name="Video-Channel-Association",
        left_type=Video,
        right_type=Channel,
    )

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def channel_id(self) -> str:
        return self.sk_id


class VideoPlaylistAssociation(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.ManyToManyRelationshipType(
        name="Video-Playlist-Association",
        left_type=Video,
        right_type=Playlist,
    )

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def playlist_id(self) -> str:
        return self.sk_id


class ViewerSubscribeYoutuber(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.ManyToManyRelationshipType(
        name="Video-Subscribe-Youtuber",
        left_type=User,
        right_type=User,
    )

    @property
    def viewer_id(self) -> str:
        return self.pk_id

    @property
    def youtuber_id(self) -> str:
        return self.sk_id


class ViewerSubscribeChannel(Entity):

    Meta = Meta

    lookup_index = LookupIndex()

    ITEM_TYPE = rl.ManyToManyRelationshipType(
        name="Viewer-Subscribe-Channel",
        left_type=User,
        right_type=Channel,
    )

    @property
    def viewer_id(self) -> str:
        return self.pk_id

    @property
    def channel_id(self) -> str:
        return self.sk_id


T_Entity = T.Union[
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

T_Entity_Type = T.Union[
    T.Type[Entity],
    T.Type[User],
    T.Type[Video],
    T.Type[Channel],
    T.Type[Playlist],
    T.Type[VideoOwnership],
    T.Type[ChannelOwnership],
    T.Type[PlaylistOwnership],
    T.Type[VideoChannelAssociation],
    T.Type[VideoPlaylistAssociation],
    T.Type[ViewerSubscribeYoutuber],
    T.Type[ViewerSubscribeChannel],
]


class UserIterProxy(IterProxy[User]):
    pass


class VideoIterProxy(IterProxy[Video]):
    pass


class ChannelIterProxy(IterProxy[Channel]):
    pass


class PlaylistIterProxy(IterProxy[Playlist]):
    pass


class VideoOwnershipIterProxy(IterProxy[VideoOwnership]):
    pass


class ChannelOwnershipIterProxy(IterProxy[ChannelOwnership]):
    pass


class PlaylistOwnershipIterProxy(IterProxy[PlaylistOwnership]):
    pass


class VideoChannelAssociationIterProxy(IterProxy[VideoChannelAssociation]):
    pass


class VideoPlaylistAssociationIterProxy(IterProxy[VideoPlaylistAssociation]):
    pass


class ViewerSubscribeYoutuberIterProxy(IterProxy[ViewerSubscribeYoutuber]):
    pass


class ViewerSubscribeChannelIterProxy(IterProxy[ViewerSubscribeChannel]):
    pass
