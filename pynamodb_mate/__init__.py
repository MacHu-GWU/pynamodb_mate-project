# -*- coding: utf-8 -*-

from ._version import __version__

__short_description__ = "Provide Addtional Features for pynamodb"
__github_username__ = "MacHu-GWU"
__license__ = "MIT"
__author__ = "Sanhe Hu"
__author_email__ = "husanhe@gmail.com"
__maintainer__ = __author__
__maintainer_email__ = __author_email__


try:
    from .attributes.encrypted import (
        EncryptedNumberAttribute,
        EncryptUnicodeAttribute,
        EncryptBinaryAttribute,
        EncryptedJsonAttribute,
    )
    from .attributes.s3backed import (
        S3BackedBigBinaryAttribute,
        S3BackedBigTextAttribute,
    )
except ImportError:
    pass
except:
    raise


try:
    from pynamodb.constants import (
        PAY_PER_REQUEST_BILLING_MODE,
        PROVISIONED_BILLING_MODE,
    )
    from pynamodb.models import (
        Model,
    )
    from pynamodb.attributes import (
        UnicodeAttribute,
        BinaryAttribute,
        NumberAttribute,
        BooleanAttribute,
        UnicodeSetAttribute,
        BinarySetAttribute,
        NumberSetAttribute,
        ListAttribute,
        MapAttribute,
        DynamicMapAttribute,
        JSONAttribute,
        UTCDateTimeAttribute,
    )
except ImportError as e:
    print(e)
except:
    raise
