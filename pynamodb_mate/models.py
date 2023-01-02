# -*- coding: utf-8 -*-

"""
Enhance the pynamodb.models.Model class.
"""

import typing as T
import copy as copy_lib

from pynamodb.models import (
    Model as PynamodbModel,
)
from pynamodb.settings import OperationSettings
from pynamodb.exceptions import DeleteError


class ConsoleUrlMaker:
    """
    Create common AWS Dynamodb Console url.
    """

    def table_overview(
        self,
        region_name: str,
        table_name: str,
    ) -> str:
        """
        Create the AWS Console url that can preview Dynamodb Table overview.
        """
        return (
            f"https://{region_name}.console.aws.amazon.com/dynamodbv2/"
            f"home?region={region_name}#"
            f"table?initialTagKey=&name={table_name}&tab=overview"
        )

    def table_items(
        self,
        region_name: str,
        table_name: str,
    ) -> str:
        """
        Create the AWS Console url that can preview items in Dynamodb Table.
        """
        return (
            f"https://{region_name}.console.aws.amazon.com/dynamodbv2/"
            f"home?region={region_name}#item-explorer?"
            f"initialTagKey=&maximize=true&table={table_name}"
        )

    def item_detail(
        self,
        region_name: str,
        table_name: str,
        hash_key: str,
        range_key: T.Optional[str] = None,
    ) -> str:
        """
        Create the AWS Console url that can preview specific Dynamodb item.
        """
        if range_key is None:
            range_key_param = "sk"
        else:
            range_key_param = f"sk={range_key}"
        return (
            f"https://{region_name}.console.aws.amazon.com/dynamodbv2/"
            f"home?region={region_name}#"
            f"edit-item?table={table_name}&itemMode=2&"
            f"pk={hash_key}&"
            f"{range_key_param}&"
            f"ref=%23item-explorer%3Ftable%3D{table_name}&"
            f"route=ROUTE_ITEM_EXPLORER"
        )


console_url_maker = ConsoleUrlMaker()


class Model(PynamodbModel):
    """
    Pynamodb Model with additional features.
    """

    def __init__(
        self,
        hash_key: T.Optional[T.Any] = None,
        range_key: T.Optional[T.Any] = None,
        **attributes,
    ):
        super().__init__(hash_key, range_key, **attributes)
        self.__post_init__()

    def __post_init__(self):
        """
        Allow user to customize the post init behavior.
        For example, it can be used to validate the data.
        """
        pass

    def to_dict(self, copy=False) -> dict:
        """
        Access the item data as a dictionary.
        """
        if copy:
            return copy_lib.deepcopy(self.attribute_values)
        else:
            return self.attribute_values

    @classmethod
    def get_one_or_none(
        cls,
        hash_key: T.Any,
        range_key: T.Optional[T.Any] = None,
        consistent_read: bool = False,
        attributes_to_get: T.Optional[T.Sequence[str]] = None,
        settings: OperationSettings = OperationSettings.default,
    ) -> T.Optional["Model"]:
        """
        Get one Dynamodb item object or None if not exists.
        """
        try:
            return cls.get(
                hash_key=hash_key,
                range_key=range_key,
                consistent_read=consistent_read,
                attributes_to_get=attributes_to_get,
                settings=settings,
            )
        except cls.DoesNotExist:
            return None

    def delete_if_exists(self) -> bool:
        """
        Delete the item if exists. Return True if exists.
        """
        hash_key_attr = self.__class__._hash_key_attribute()
        range_key_attr = self.__class__._range_key_attribute()
        condition = hash_key_attr.exists()
        if range_key_attr:
            condition &= range_key_attr.exists()
        try:
            self.delete(condition=condition)
            return True
        except DeleteError:
            return False

    @classmethod
    def delete_all(cls) -> int:
        """
        Delete all item in a Dynamodb table by scanning all item and delete.
        """
        ith = 0
        with cls.batch_write() as batch:
            for ith, item in enumerate(cls.scan(), start=1):
                batch.delete(item)
        return ith

    @classmethod
    def get_table_overview_console_url(cls) -> str:
        """
        Create the AWS Console url that can preview Dynamodb Table settings.
        """
        return console_url_maker.table_overview(
            region_name=cls.Meta.region,
            table_name=cls.Meta.table_name,
        )

    @classmethod
    def get_table_items_console_url(cls) -> str:
        """
        Create the AWS Console url that can preview items in Dynamodb Table.
        """
        return console_url_maker.table_items(
            region_name=cls.Meta.region,
            table_name=cls.Meta.table_name,
        )

    @property
    def item_detail_console_url(self) -> str:
        """
        Return the AWS Console url that can preview Dynamodb item data.
        """
        klass = self.__class__
        hash_key_name = klass._hash_keyname
        range_key_name = klass._range_keyname
        hash_key_attr = getattr(klass, hash_key_name)
        hash_key_value = getattr(self, hash_key_name)
        kwargs = dict(
            region_name=klass.Meta.region,
            table_name=klass.Meta.table_name,
            hash_key=hash_key_attr.serialize(hash_key_value),
        )
        if range_key_name is not None:
            range_key_attr = getattr(klass, range_key_name)
            range_key_value = getattr(self, range_key_name)
            kwargs["range_key"] = range_key_attr.serialize(range_key_value)
        return console_url_maker.item_detail(**kwargs)
