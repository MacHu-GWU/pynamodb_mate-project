# -*- coding: utf-8 -*-

import typing as T
from datetime import datetime

from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    BooleanAttribute,
    BinaryAttribute,
    UTCDateTimeAttribute,
)

REQUIRED_STR = T.Union[str, UnicodeAttribute]
OPTIONAL_STR = T.Optional[REQUIRED_STR]
REQUIRED_INT = T.Union[int, NumberAttribute]
OPTIONAL_INT = T.Optional[REQUIRED_INT]
REQUIRED_FLOAT = T.Union[float, NumberAttribute]
OPTIONAL_FLOAT = T.Optional[REQUIRED_FLOAT]
REQUIRED_BOOL = T.Union[bool, BooleanAttribute]
OPTIONAL_BOOL = T.Optional[REQUIRED_BOOL]
REQUIRED_BINARY = T.Union[bool, BinaryAttribute]
OPTIONAL_BINARY = T.Optional[REQUIRED_BINARY]
REQUIRED_DATETIME = T.Union[datetime, UTCDateTimeAttribute]
OPTIONAL_DATETIME = T.Optional[REQUIRED_DATETIME]
