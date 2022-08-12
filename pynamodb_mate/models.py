# -*- coding: utf-8 -*-

import typing as T

from pynamodb.models import (
    Model as PynamodbModel,
)


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
    Add more features later
    """

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
        return console_url_maker.table_overview(
            region_name=cls.Meta.region,
            table_name=cls.Meta.table_name,
        )

    @classmethod
    def get_table_items_console_url(cls) -> str:
        return console_url_maker.table_items(
            region_name=cls.Meta.region,
            table_name=cls.Meta.table_name,
        )

    @property
    def item_detail_console_url(self) -> str:
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
