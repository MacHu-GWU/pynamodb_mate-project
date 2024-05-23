# -*- coding: utf-8 -*-

import pynamodb_mate.api as pm


def test_api():
    _ = pm.__version__
    _ = pm.Connection
    _ = pm.GlobalSecondaryIndex
    _ = pm.LocalSecondaryIndex
    _ = pm.KeysOnlyProjection
    _ = pm.IncludeProjection
    _ = pm.AllProjection
    _ = pm.constants
    _ = pm.CustomAttribute
    _ = pm.DiscriminatorAttribute
    _ = pm.BinaryAttribute
    _ = pm.BinarySetAttribute
    _ = pm.UnicodeAttribute
    _ = pm.UnicodeSetAttribute
    _ = pm.JSONAttribute
    _ = pm.BooleanAttribute
    _ = pm.NumberAttribute
    _ = pm.NumberSetAttribute
    _ = pm.VersionAttribute
    _ = pm.TTLAttribute
    _ = pm.UTCDateTimeAttribute
    _ = pm.NullAttribute
    _ = pm.MapAttribute
    _ = pm.DynamicMapAttribute
    _ = pm.ListAttribute
    _ = pm.TransactGet
    _ = pm.TransactWrite
    _ = pm.pre_dynamodb_send
    _ = pm.post_dynamodb_send
    _ = pm.REQUIRED_STR
    _ = pm.OPTIONAL_STR
    _ = pm.REQUIRED_INT
    _ = pm.OPTIONAL_INT
    _ = pm.REQUIRED_FLOAT
    _ = pm.OPTIONAL_FLOAT
    _ = pm.REQUIRED_BOOL
    _ = pm.OPTIONAL_BOOL
    _ = pm.REQUIRED_BINARY
    _ = pm.OPTIONAL_BINARY
    _ = pm.REQUIRED_DATETIME
    _ = pm.attributes.CompressedAttribute
    _ = pm.attributes.CompressedUnicodeAttribute
    _ = pm.attributes.CompressedBinaryAttribute
    _ = pm.attributes.CompressedJSONDictAttribute
    _ = pm.attributes.SymmetricEncryptedAttribute
    _ = pm.attributes.EncryptedNumberAttribute
    _ = pm.attributes.EncryptedUnicodeAttribute
    _ = pm.attributes.EncryptedBinaryAttribute
    _ = pm.attributes.EncryptedJsonDictAttribute
    _ = pm.patterns.cache.InMemoryBackend
    _ = pm.patterns.cache.JsonDictInMemoryCache
    _ = pm.patterns.cache.JsonListInMemoryCache
    _ = pm.patterns.cache.DynamoDBBackend
    _ = pm.patterns.cache.JsonDictDynamodbCache
    _ = pm.patterns.cache.JsonListDynamodbCache
    _ = pm.patterns.cache.MultiLayerCache
    _ = pm.patterns.cache.JsonDictMultiLayerCache
    _ = pm.patterns.cache.JsonListMultiLayerCache
    _ = pm.patterns.large_attribute.split_s3_uri
    _ = pm.patterns.large_attribute.LargeAttributeMixin
    _ = pm.patterns.relationship.BaseLookupIndex
    _ = pm.patterns.relationship.BaseEntity
    _ = pm.patterns.relationship.T_BASE_ENTITY
    _ = pm.patterns.relationship.ROOT
    _ = pm.patterns.relationship.ItemType
    _ = pm.patterns.relationship.EntityType
    _ = pm.patterns.relationship.RelationshipType
    _ = pm.patterns.relationship.OneToManyRelationshipType
    _ = pm.patterns.relationship.ManyToManyRelationshipType
    _ = pm.patterns.relationship.RelationshipSetting
    _ = pm.patterns.status_tracker.TaskExecutionError
    _ = pm.patterns.status_tracker.TaskIsNotInitializedError
    _ = pm.patterns.status_tracker.TaskIsNotReadyToStartError
    _ = pm.patterns.status_tracker.TaskLockedError
    _ = pm.patterns.status_tracker.TaskAlreadySucceedError
    _ = pm.patterns.status_tracker.TaskIgnoredError
    _ = pm.patterns.status_tracker.StatusNameEnum
    _ = pm.patterns.status_tracker.BaseStatusEnum
    _ = pm.patterns.status_tracker.TrackerConfig
    _ = pm.patterns.status_tracker.StatusAndUpdateTimeIndex
    _ = pm.patterns.status_tracker.BaseTask
    _ = pm.patterns.status_tracker.ExecutionContext


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.api")
