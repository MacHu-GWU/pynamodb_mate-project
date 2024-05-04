# -*- coding: utf-8 -*-

import typing as T

import pynamodb_mate as pm
import pynamodb_mate.patterns.relationship.api as rl
from iterproxy import IterProxy


class LookupIndex(rl.BaseLookupIndex):
    class Meta:
        index_name = "lookup-index"
        projection = pm.AllProjection()


class Entity(rl.BaseEntity):
    """
    :param pk: partition key can only has alpha letter and hyphen.
    """

    class Meta:
        table_name = "entity"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    lookup_index = LookupIndex()

    def print_vip_attrs(self):
        print(self.get_vip_attrs())


class User(Entity):
    lookup_index = LookupIndex()

    @property
    def user_id(self) -> str:
        return self.pk_id


class Document(Entity):
    lookup_index = LookupIndex()

    @property
    def doc_id(self) -> str:
        return self.pk_id


class Channel(Entity):
    lookup_index = LookupIndex()

    @property
    def channel_id(self) -> str:
        return self.pk_id


class Playlist(Entity):
    lookup_index = LookupIndex()

    @property
    def playlist_id(self) -> str:
        return self.pk_id


class VideoOwnership(Entity):
    lookup_index = LookupIndex()

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class ChannelOwnership(Entity):
    lookup_index = LookupIndex()

    @property
    def channel_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class PlaylistOwnership(Entity):
    lookup_index = LookupIndex()

    @property
    def playlist_id(self) -> str:
        return self.pk_id

    @property
    def user_id(self) -> str:
        return self.sk_id


class VideoChannelAssociation(Entity):
    lookup_index = LookupIndex()

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def channel_id(self) -> str:
        return self.sk_id


class VideoPlaylistAssociation(Entity):
    lookup_index = LookupIndex()

    @property
    def video_id(self) -> str:
        return self.pk_id

    @property
    def playlist_id(self) -> str:
        return self.sk_id


class ViewerSubscribeYoutuber(Entity):
    lookup_index = LookupIndex()

    @property
    def viewer_id(self) -> str:
        return self.pk_id

    @property
    def youtuber_id(self) -> str:
        return self.sk_id


class ViewerSubscribeChannel(Entity):
    lookup_index = LookupIndex()

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


user_entity_type = rl.EntityType(name="User", klass=User)
video_entity_type = rl.EntityType(name="Video", klass=Video)
channel_entity_type = rl.EntityType(name="Channel", klass=Channel)
playlist_entity_type = rl.EntityType(name="Playlist", klass=Playlist)

video_ownership_relationship_type = rl.OneToManyRelationshipType(
    name="Video-Ownership",
    klass=VideoOwnership,
    one_type=user_entity_type,
    many_type=video_entity_type,
)
channel_ownership_relationship_type = rl.OneToManyRelationshipType(
    name="Channel-Ownership",
    klass=ChannelOwnership,
    one_type=user_entity_type,
    many_type=channel_entity_type,
)
playlist_ownership_relationship_type = rl.OneToManyRelationshipType(
    name="Playlist-Ownership",
    klass=PlaylistOwnership,
    one_type=user_entity_type,
    many_type=playlist_entity_type,
)

video_channel_association_relationship_type = rl.ManyToManyRelationshipType(
    name="Video-Channel-Association",
    klass=VideoChannelAssociation,
    left_type=video_entity_type,
    right_type=channel_entity_type,
)
video_playlist_association_relationship_type = rl.ManyToManyRelationshipType(
    name="Video-Playlist-Association",
    klass=VideoPlaylistAssociation,
    left_type=video_entity_type,
    right_type=playlist_entity_type,
)
viewer_subscribe_youtuber_relationship_type = rl.ManyToManyRelationshipType(
    name="Viewer-Subscribe-Youtuber",
    klass=ViewerSubscribeYoutuber,
    left_type=user_entity_type,
    right_type=user_entity_type,
)
viewer_subscribe_channel_relationship_type = rl.ManyToManyRelationshipType(
    name="Viewer-Subscribe-Channel",
    klass=ViewerSubscribeChannel,
    left_type=user_entity_type,
    right_type=channel_entity_type,
)


class RelationshipSetting(rl.RelationshipSetting):
    def new_user(
        self,
        id: str,
        name: str,
        save: bool = True,
    ) -> T.Optional[User]:
        return self.new_entity(e_type=user_entity_type, id=id, name=name, save=save)

    def new_video(
        self,
        id: str,
        name: str,
        save: bool = True,
    ) -> T.Optional[Video]:
        return self.new_entity(e_type=video_entity_type, id=id, name=name, save=save)

    def new_channel(
        self,
        id: str,
        name: str,
        save: bool = True,
    ) -> T.Optional[Channel]:
        return self.new_entity(e_type=channel_entity_type, id=id, name=name, save=save)

    def new_playlist(
        self,
        id: str,
        name: str,
        save: bool = True,
    ) -> T.Optional[Playlist]:
        return self.new_entity(e_type=playlist_entity_type, id=id, name=name, save=save)

    def list_users(self) -> UserIterProxy:
        return self.list_entities(entity_type=user_entity_type)

    def list_videos(self) -> UserIterProxy:
        return self.list_entities(entity_type=video_entity_type)

    def list_channels(self) -> UserIterProxy:
        return self.list_entities(entity_type=channel_entity_type)

    def list_playlists(self) -> UserIterProxy:
        return self.list_entities(entity_type=playlist_entity_type)

    def set_video_owner(
        self,
        conn: pm.Connection,
        video_id: str,
        user_id: str,
    ):
        self.set_one_to_many(
            conn=conn,
            one_to_many_r_type=video_ownership_relationship_type,
            many_entity_id=video_id,
            one_entity_id=user_id,
        )

    def set_channel_owner(
        self,
        conn: pm.Connection,
        channel_id: str,
        user_id: str,
    ):
        self.set_one_to_many(
            conn=conn,
            one_to_many_r_type=channel_ownership_relationship_type,
            many_entity_id=channel_id,
            one_entity_id=user_id,
        )

    def set_playlist_owner(
        self,
        conn: pm.Connection,
        playlist_id: str,
        user_id: str,
    ):
        self.set_one_to_many(
            conn=conn,
            one_to_many_r_type=playlist_ownership_relationship_type,
            many_entity_id=playlist_id,
            one_entity_id=user_id,
        )

    def find_videos_created_by_a_user(
        self,
        user_id: str,
    ) -> VideoIterProxy:
        return self.find_many_by_one(
            one_to_many_r_type=video_ownership_relationship_type,
            one_entity_id=user_id,
        )

    def find_channels_created_by_a_user(
        self,
        user_id: str,
    ) -> ChannelIterProxy:
        return self.find_many_by_one(
            one_to_many_r_type=channel_ownership_relationship_type,
            one_entity_id=user_id,
        )

    def find_playlists_created_by_a_user(
        self,
        user_id: str,
    ) -> PlaylistIterProxy:
        return self.find_many_by_one(
            one_to_many_r_type=playlist_ownership_relationship_type,
            one_entity_id=user_id,
        )

    def add_video_to_channel(
        self,
        video_id: str,
        channel_id: str,
    ):
        self.set_many_to_many(
            many_to_many_r_type=video_channel_association_relationship_type,
            left_entity_id=video_id,
            right_entity_id=channel_id,
        )

    def add_video_to_playlist(
        self,
        video_id: str,
        playlist_id: str,
    ):
        self.set_many_to_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            left_entity_id=video_id,
            right_entity_id=playlist_id,
        )

    def viewer_subscribe_youtuber(
        self,
        viewer_id: str,
        youtuber_id: str,
    ):
        self.set_many_to_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            left_entity_id=viewer_id,
            right_entity_id=youtuber_id,
        )

    def viewer_subscribe_channel(
        self,
        viewer_id: str,
        channel_id: str,
    ):
        self.set_many_to_many(
            many_to_many_r_type=viewer_subscribe_channel_relationship_type,
            left_entity_id=viewer_id,
            right_entity_id=channel_id,
        )

    def find_videos_in_channel(
        self,
        channel_id: str,
    ) -> VideoChannelAssociationIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=video_channel_association_relationship_type,
            entity_id=channel_id,
            lookup_by_left=False,
        )

    def find_channels_that_has_video(
        self,
        video_id: str,
    ) -> VideoChannelAssociationIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=video_channel_association_relationship_type,
            entity_id=video_id,
            lookup_by_left=True,
        )

    def find_videos_in_playlist(
        self,
        playlist_id: str,
    ) -> VideoPlaylistAssociationIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            entity_id=playlist_id,
            lookup_by_left=False,
        )

    def find_playlists_that_has_video(
        self,
        video_id: str,
    ) -> VideoPlaylistAssociationIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            entity_id=video_id,
            lookup_by_left=True,
        )

    def find_subscribers_for_youtuber(
        self,
        youtuber_id: str,
    ) -> ViewerSubscribeYoutuberIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            entity_id=youtuber_id,
            lookup_by_left=False,
        )

    def find_subscribed_youtubers(
        self,
        user_id: str,
    ) -> ViewerSubscribeYoutuberIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            entity_id=user_id,
            lookup_by_left=True,
        )

    def find_subscribers_for_channel(
        self,
        channel_id: str,
    ) -> ViewerSubscribeChannelIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=viewer_subscribe_channel_relationship_type,
            entity_id=channel_id,
            lookup_by_left=False,
        )

    def find_subscribed_channels(
        self,
        user_id: str,
    ) -> ViewerSubscribeChannelIterProxy:
        return self.find_many_by_many(
            many_to_many_r_type=viewer_subscribe_channel_relationship_type,
            entity_id=user_id,
            lookup_by_left=True,
        )

    def remove_video_from_channel(
        self,
        video_id: str,
        channel_id: str,
    ):
        self.unset_many_to_many(
            many_to_many_r_type=video_channel_association_relationship_type,
            left_entity_id=video_id,
            right_entity_id=channel_id,
        )

    def remove_video_from_playlist(
        self,
        video_id: str,
        playlist_id: str,
    ):
        self.unset_many_to_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            left_entity_id=video_id,
            right_entity_id=playlist_id,
        )

    def viewer_unsubscribe_youtuber(
        self,
        viewer_id: str,
        youtuber_id: str,
    ):
        self.unset_many_to_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            left_entity_id=viewer_id,
            right_entity_id=youtuber_id,
        )

    def viewer_unsubscribe_channel(
        self,
        viewer_id: str,
        channel_id: str,
    ):
        self.unset_many_to_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            left_entity_id=viewer_id,
            right_entity_id=channel_id,
        )

    def clear_channel(
        self,
        channel_id: str,
    ):
        self.clear_many_by_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            entity_id=channel_id,
            lookup_by_left=False,
        )

    def clear_playlist(
        self,
        playlist_id: str,
    ):
        self.clear_many_by_many(
            many_to_many_r_type=video_playlist_association_relationship_type,
            entity_id=playlist_id,
            lookup_by_left=False,
        )

    def unsubscribe_all_youtuber(
        self,
        viewer_id: str,
    ):
        self.clear_many_by_many(
            many_to_many_r_type=viewer_subscribe_youtuber_relationship_type,
            entity_id=viewer_id,
            lookup_by_left=True,
        )

    def unsubscribe_all_channel(
        self,
        viewer_id: str,
    ):
        self.clear_many_by_many(
            many_to_many_r_type=viewer_subscribe_channel_relationship_type,
            entity_id=viewer_id,
            lookup_by_left=True,
        )


r_setting = RelationshipSetting(
    main_model=Entity,
    entity_types=[
        user_entity_type,
        video_entity_type,
        channel_entity_type,
        playlist_entity_type,
    ],
    one_to_many_relationship_types=[
        video_ownership_relationship_type,
        channel_ownership_relationship_type,
        playlist_ownership_relationship_type,
    ],
    many_to_many_relationship_types=[
        video_channel_association_relationship_type,
        video_playlist_association_relationship_type,
        viewer_subscribe_youtuber_relationship_type,
        viewer_subscribe_channel_relationship_type,
    ],
)
