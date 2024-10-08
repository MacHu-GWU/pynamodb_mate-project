# -*- coding: utf-8 -*-

"""
The user can define the relationship (one-to-many, many-to-many) between entities.

There are three types of DynamoDB item:

- Entity: the main item that represents the entity.
- OneToManyRelationship: the item that represents the one-to-many relationship.
- ManyToManyRelationship: the item that represents the many-to-many relationship.

Let's use YouTube as an example:

- Entity: User, Video, Channel, Playlist.
- OneToManyRelationship: Video Ownership, Channel Ownership, Playlist Ownership.
- ManyToManyRelationship: Video Channel Association, Video Playlist Association,
    User Subscription, Channel Subscription.

All three types of items has to have a unique name. The name will be used in
partition key, sort key and type attribute naming convention. I recommend to
keep the name short and simple.

One the user declared the relationship metadata, the :class:`RelationshipSetting`
will be a helper class to provide lots of utility functions to Create, Update,
Delete and Select items by relationship.
"""

try:
    import typing_extensions as T
except ImportError:  # pragma: no cover
    import typing as T

import uuid
import hashlib
import dataclasses
from datetime import datetime, timezone

import pynamodb.exceptions as exc
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex
from pynamodb.transactions import TransactWrite
from pynamodb.connection import Connection

from iterproxy import IterProxy

from ...type_hint import (
    REQUIRED_STR,
    OPTIONAL_STR,
    REQUIRED_BOOL,
    REQUIRED_DATETIME,
)
from ...models import Model


ROOT = "--root--"


# ------------------------------------------------------------------------------
# Entity relationship helpers
# ------------------------------------------------------------------------------
def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def validate_entity_id(entity_id: str):  # pragma: no cover
    if "_" in entity_id:
        raise ValueError(f"entity id {entity_id!r} cannot contain underscore")


def validate_item_type_name(name: str):  # pragma: no cover
    if "_" in name:
        raise ValueError(f"item type name {name!r} cannot contain underscore")


@dataclasses.dataclass
class ItemType:
    """ """

    name: str = dataclasses.field()

    def __post_init__(self):
        validate_item_type_name(self.name)


@dataclasses.dataclass
class EntityType(ItemType):
    pass


@dataclasses.dataclass
class RelationshipType(ItemType):
    pass


@dataclasses.dataclass
class OneToManyRelationshipType(ItemType):
    """
    one-to-many relationship. For example, "one" Google account can have
    "many" YouTube videos.

    The "many" entity id, YouTube video id always be the partition key,
    and the "one" entity id, Google account id always be the sort key.

    :param one_type: the "one" entity type.
    :param many_type: the "many" entity type.
    """

    one_type: T.Type["T_BASE_ENTITY"] = dataclasses.field()
    many_type: T.Type["T_BASE_ENTITY"] = dataclasses.field()


@dataclasses.dataclass
class ManyToManyRelationshipType(ItemType):
    """
    many-to-many relationship. For example, a playlist can have many videos,
    and a video can be in many playlists. It is critical to know which entity
    is on the left and which entity is on the right. Because the left entity
    and the right entity could be the same in certain relationship. For example,
    user can subscribe another user.

    :param left_type: the left entity type.
    :param right_type: the right entity type.
    """

    left_type: T.Type["T_BASE_ENTITY"] = dataclasses.field()
    right_type: T.Type["T_BASE_ENTITY"] = dataclasses.field()


T_ITEM_TYPE = T.Union[EntityType, OneToManyRelationshipType, ManyToManyRelationshipType]


class BaseLookupIndex(GlobalSecondaryIndex):
    """
    The lookup index uses the sort key as the hash key to provide reverse lookup
    capability.
    """

    sk: REQUIRED_STR = UnicodeAttribute(hash_key=True)


class BaseEntity(Model):
    """
    Main entity item. Base class for all entity items and relationship items.
    In DynamoDB, we put all kinds of entities into the same table, and use
    the type attribute to distinguish them.

    It has to have a :class:`BaseLookupIndex` as the lookup index. You can declare
    more index as needed.

    :param pk: partition key can only have alpha letter and hyphen.
        You can NOT use underscore in the partition key.
        For entity item, it is the unique id.
    :param sk: sort key can only have alpha letter and hyphen.
    For entity item, it is always "${entity_id}_--root--". For relationship item,
        pk and sk are the two unique ids of the two related entities.
    :param type: item type, can be used to filter by the type.
    :param name: human friendly name of the entity.
    :param create_at: the creation time of the entity.
    :param update_at: the last update time of the entity.
    :param deleted: if True, the entity is deleted (softly).
    """

    # partition key and sort key
    pk: REQUIRED_STR = UnicodeAttribute(hash_key=True)
    sk: REQUIRED_STR = UnicodeAttribute(range_key=True)

    # common attributes
    type: REQUIRED_STR = UnicodeAttribute()
    name: OPTIONAL_STR = UnicodeAttribute(null=True)
    create_at: REQUIRED_DATETIME = UTCDateTimeAttribute(null=False)
    update_at: REQUIRED_DATETIME = UTCDateTimeAttribute(null=False)
    deleted: REQUIRED_BOOL = BooleanAttribute(default=False)

    lookup_index: "BaseLookupIndex"

    ITEM_TYPE: "T_ITEM_TYPE"

    @property
    def pk_id(self):
        return self.pk.split("_")[0]

    @property
    def sk_id(self):
        return self.sk.split("_")[0]

    def get_vip_attrs(self) -> T.Dict[str, T.Any]:  # pragma: no cover
        """
        Get all important attributes for the entity.
        """
        d = dict(
            type=self.type,
            pk=self.pk_id,
            sk=self.sk_id,
        )
        if self.name:
            d["name"] = self.name
        return d

    @classmethod
    def new_entity(
        cls,
        id: str,
        name: str,
        save: bool = True,
        **kwargs,
    ) -> T.Optional[T.Self]:
        """
        Create a new entity.

        :param e_type:
        :param id: unique id for the entity.
        :param name: human-friendly name for the entity.
        :param save: if True, save the entity to DynamoDB. Otherwise,
            just create the in-memory entity.
        :param kwargs: additional parameters for the constructor.
        """
        validate_entity_id(id)
        now = get_utc_now()
        entity = cls(
            pk=id,
            sk=f"{cls.ITEM_TYPE.name}_{ROOT}",
            type=cls.ITEM_TYPE.name,
            name=name,
            create_at=now,
            update_at=now,
            **kwargs,
        )
        if save is False:  # pragma: no cover
            return entity
        try:
            # ensure that the entity does not exist
            res = entity.save(
                condition=(~cls.pk.exists()),
            )
            return entity
        except exc.PutError as e:  # pragma: no cover
            return None

    @classmethod
    def get_entity(
        cls,
        id: str,
        consistent_read: bool = False,
        attributes_to_get: T.Optional[T.Sequence[str]] = None,
    ) -> T.Optional[T.Self]:
        return cls.get_one_or_none(
            hash_key=id,
            range_key=f"{cls.ITEM_TYPE.name}_{ROOT}",
            consistent_read=consistent_read,
            attributes_to_get=attributes_to_get,
        )

    # todo: add support to use more kwargs
    @classmethod
    def list_entity(
        cls,
    ) -> T.Iterable["T_BASE_ENTITY"]:
        result = cls.lookup_index.query(
            hash_key=f"{cls.ITEM_TYPE.name}_{ROOT}",
            filter_condition=(cls.type == cls.ITEM_TYPE.name),
        )
        return BaseEntityIterProxy(result)

    @classmethod
    def set_one_to_many(
        cls,
        conn: Connection,
        many_entity_id: str,
        one_entity_id: str,
        client_request_token: T.Optional[str] = None,
    ):
        """
        For example, in YouTube use case, one user has many videos,
        one video only belongs to one user. Then, this function is used to
        set ownership of a video. In this case, the video is the many entity,
        the user is the one entity.

        If a video already has an owner, this function will delete the old
        relationship first then create a new relationship.

        :param conn: ``pynamodb_mate.Connection`` object.
        :param many_entity_id: the many entity id.
        :param one_entity_id: the one entity id.
        """
        type = cls.ITEM_TYPE.name
        if client_request_token is None:
            client_request_token = hashlib.md5(
                f"set_{many_entity_id}_{one_entity_id}_{type}_{uuid.uuid4().hex}".encode(
                    "utf-8"
                )
            ).hexdigest()
        with TransactWrite(
            connection=conn,
            client_request_token=client_request_token,
        ) as trans:
            # find all existing relationship entities and delete them
            r_entities = list(
                cls.query(
                    hash_key=f"{many_entity_id}_{type}",
                )
            )
            for r_entity in r_entities:
                trans.delete(r_entity)
            # create a new relationship entity
            now = get_utc_now()
            r_entity = cls(
                pk=f"{many_entity_id}_{type}",
                sk=f"{one_entity_id}_{type}",
                type=type,
                create_at=now,
                update_at=now,
            )
            trans.save(r_entity)

    @classmethod
    def unset_one_to_many(
        cls,
        conn: Connection,
        many_entity_id: str,
        client_request_token: T.Optional[str] = None,
    ):  # pragma: no cover
        """
        Unset the one-to-many relationship.

        :param conn: ``pynamodb_mate.Connection`` object.
        :param many_entity_id: the many entity id.
        """
        type = cls.ITEM_TYPE.name
        if client_request_token is None:
            client_request_token = hashlib.md5(
                f"unset_{many_entity_id}_{type}_{uuid.uuid4().hex}".encode("utf-8")
            ).hexdigest()
        with TransactWrite(
            connection=conn,
            client_request_token=client_request_token,
        ) as trans:
            # find all existing relationship entities and delete them
            r_entities = list(
                cls.query(
                    hash_key=f"{many_entity_id}_{type}",
                )
            )
            for r_entity in r_entities:
                trans.delete(r_entity)

    @classmethod
    def find_one_by_many(
        cls,
        many_entity_id: str,
    ) -> T.Optional["T_BASE_ENTITY"]:
        """
        For example, in YouTube use case, one user has "many" YouTube videos.
        This function will find the owner of the given YouTube video.

        :param many_entity_id: the many entity id.
        """
        type = cls.ITEM_TYPE.name
        return cls.iter_query(
            hash_key=f"{many_entity_id}_{type}",
        ).one_or_none()

    @classmethod
    def find_many_by_one(
        cls,
        one_entity_id: str,
    ) -> T.Iterable["T_BASE_ENTITY"]:
        """
        For example, in YouTube use case, one user has "many" YouTube videos.
        This function will find the all videos owned by the given user.

        :param one_entity_id: the one entity id.
        """
        type = cls.ITEM_TYPE.name
        result = cls.lookup_index.query(
            hash_key=f"{one_entity_id}_{type}",
        )
        return BaseEntityIterProxy(result)

    @classmethod
    def set_many_to_many(
        cls,
        left_entity_id: str,
        right_entity_id: str,
    ):
        """
        For example, in YouTube use case, one playlist has "many" videos.
        One video can be in "many" playlists. This function will add the
        video to the playlist.

        :param left_entity_id: the left entity id.
        :param right_entity_id: the right entity id.
        """
        type = cls.ITEM_TYPE.name
        now = get_utc_now()
        cls(
            pk=f"{left_entity_id}_{type}",
            sk=f"{right_entity_id}_{type}",
            type=type,
            create_at=now,
            update_at=now,
        ).save(
            condition=~(cls.pk.exists() & cls.sk.exists()),
        )

    @classmethod
    def unset_many_to_many(
        cls,
        left_entity_id: str,
        right_entity_id: str,
    ):  # pragma: no cover
        """
        For example, in YouTube use case, one playlist has "many" videos.
        One video can be in "many" playlists. This function will remove the
        video from the playlist.

        :param left_entity_id: the left entity id.
        :param right_entity_id: the right entity id.
        """
        type = cls.ITEM_TYPE.name
        now = get_utc_now()
        cls(
            pk=f"{left_entity_id}_{type}",
            sk=f"{right_entity_id}_{type}",
            type=type,
            create_at=now,
            update_at=now,
        ).delete(
            condition=(cls.pk.exists() & cls.sk.exists()),
        )

    @classmethod
    def find_many_by_many(
        cls,
        entity_id: str,
        lookup_by_left: bool,
    ) -> T.Iterable["T_BASE_ENTITY"]:
        """
        In many-to-many relationship, for example, "one" Youtube viewer can
        subscribe "many" Youtube channels, and "one" Youtube channel can be
        subscribed by "many" Youtube viewers. In this relationship, the
        viewer is on the left and channel is on the right.

        If lookup_by_left is True, this function will find all channels that
        the given viewer has subscribed. If lookup_by_left is False, this
        function will find all viewers who have subscribed the given channel.

        :param entity_id: the entity id.
        :param lookup_by_left: if True, find all items by the left entity id.
            otherwise, find all items by the right entity id.
        """
        type = cls.ITEM_TYPE.name
        if lookup_by_left:
            result = cls.query(
                hash_key=f"{entity_id}_{type}",
            )
        else:
            result = cls.lookup_index.query(
                hash_key=f"{entity_id}_{type}",
            )
        return BaseEntityIterProxy(result)

    @classmethod
    def clear_many_by_many(
        cls,
        entity_id: str,
        lookup_by_left: bool,
    ):
        """
        Clear all many-to-many relationship items.

        :param entity_id: the entity id.
        :param lookup_by_left: if True, find all items by the left entity id.
            otherwise, find all items by the right entity id.
        """
        item_list = list(
            cls.find_many_by_many(
                entity_id=entity_id,
                lookup_by_left=lookup_by_left,
            )
        )
        with cls.batch_write() as batch:
            for item in item_list:
                batch.delete(item)


T_BASE_ENTITY = T.TypeVar("T_BASE_ENTITY", bound=BaseEntity)


class BaseEntityIterProxy(IterProxy[T_BASE_ENTITY]):
    pass
