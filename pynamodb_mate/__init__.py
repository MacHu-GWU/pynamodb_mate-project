# -*- coding: utf-8 -*-

from ._version import __version__

__short_description__ = "Provide Additional Features for pynamodb."
__github_username__ = "MacHu-GWU"
__license__ = "MIT"
__author__ = "Sanhe Hu"
__author_email__ = "husanhe@gmail.com"
__maintainer__ = __author__
__maintainer_email__ = __author_email__


try:
    from pynamodb.connection import Connection
    from pynamodb.indexes import (
        GlobalSecondaryIndex,
        LocalSecondaryIndex,
        KeysOnlyProjection,
        IncludeProjection,
        AllProjection,
    )
    from pynamodb.constants import (
        BINARY,
        BINARY_SET,
        BOOLEAN,
        LIST,
        MAP,
        NULL,
        NUMBER,
        NUMBER_SET,
        STRING,
        STRING_SET,
        PAY_PER_REQUEST_BILLING_MODE,
        PROVISIONED_BILLING_MODE,
    )
    from pynamodb.attributes import (
        Attribute as CustomAttribute,
        DiscriminatorAttribute,
        BinaryAttribute,
        BinarySetAttribute,
        UnicodeAttribute,
        UnicodeSetAttribute,
        JSONAttribute,
        BooleanAttribute,
        NumberAttribute,
        NumberSetAttribute,
        VersionAttribute,
        TTLAttribute,
        UTCDateTimeAttribute,
        NullAttribute,
        MapAttribute,
        DynamicMapAttribute,
        ListAttribute,
    )
    from pynamodb.transactions import (
        TransactGet,
        TransactWrite,
    )
    from pynamodb.signals import pre_dynamodb_send, post_dynamodb_send
except ImportError as e:  # pragma: no cover
    print(e)
    pass
except:  # pragma: no cover
    raise


try:
    from .attributes.s3backed import (
        S3BackedAttribute,
        S3BackedBigBinaryAttribute,
        S3BackedBigTextAttribute,
        S3BackedJsonDictAttribute,
    )
    from .attributes.compressed import (
        CompressedAttribute,
        CompressedUnicodeAttribute,
        CompressedBinaryAttribute,
        CompressedJSONDictAttribute,
    )
    from .models import Model
except ImportError as e:  # pragma: no cover
    pass
except:  # pragma: no cover
    raise


try:
    from .attributes.encrypted import (
        SymmetricEncryptedAttribute,
        EncryptedNumberAttribute,
        EncryptedUnicodeAttribute,
        EncryptedBinaryAttribute,
        EncryptedJsonDictAttribute,
    )
except ImportError as e:  # pragma: no cover
    pass
except:  # pragma: no cover
    raise


try:
    from . import patterns
except ImportError as e:  # pragma: no cover
    pass
except:  # pragma: no cover
    raise
