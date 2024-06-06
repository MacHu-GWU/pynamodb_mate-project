# -*- coding: utf-8 -*-

"""
Usage example::

    import pynamodb_mate.api as pm
"""

from ._version import __version__
from pynamodb.connection import Connection
from pynamodb.indexes import GlobalSecondaryIndex
from pynamodb.indexes import LocalSecondaryIndex
from pynamodb.indexes import KeysOnlyProjection
from pynamodb.indexes import IncludeProjection
from pynamodb.indexes import AllProjection
from pynamodb import constants
from pynamodb.attributes import Attribute as CustomAttribute
from pynamodb.attributes import DiscriminatorAttribute
from pynamodb.attributes import BinaryAttribute
from pynamodb.attributes import BinarySetAttribute
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import UnicodeSetAttribute
from pynamodb.attributes import JSONAttribute
from pynamodb.attributes import BooleanAttribute
from pynamodb.attributes import NumberAttribute
from pynamodb.attributes import NumberSetAttribute
from pynamodb.attributes import VersionAttribute
from pynamodb.attributes import TTLAttribute
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.attributes import NullAttribute
from pynamodb.attributes import MapAttribute
from pynamodb.attributes import DynamicMapAttribute
from pynamodb.attributes import ListAttribute
from pynamodb.transactions import TransactGet
from pynamodb.transactions import TransactWrite
from pynamodb.signals import pre_dynamodb_send
from pynamodb.signals import post_dynamodb_send
from .type_hint import REQUIRED_STR
from .type_hint import OPTIONAL_STR
from .type_hint import REQUIRED_INT
from .type_hint import OPTIONAL_INT
from .type_hint import REQUIRED_FLOAT
from .type_hint import OPTIONAL_FLOAT
from .type_hint import REQUIRED_BOOL
from .type_hint import OPTIONAL_BOOL
from .type_hint import REQUIRED_BINARY
from .type_hint import OPTIONAL_BINARY
from .type_hint import REQUIRED_DATETIME
from .type_hint import OPTIONAL_DATETIME
from .attributes import api as attributes
from .models import Model
from .models import T_MODEL
from .patterns import api as patterns
