# -*- coding: utf-8 -*-

"""
Use DynamoDB as a cache backend.
"""

from .backend.in_memory import (
    InMemoryBackend,
    JsonDictInMemoryCache,
    JsonListInMemoryCache,
)
from .backend.dynamodb import (
    DynamoDBBackend,
    JsonDictDynamodbCache,
    JsonListDynamodbCache,
)
from .multi_layer import (
    MultiLayerCache,
    JsonDictMultiLayerCache,
    JsonListMultiLayerCache,
)