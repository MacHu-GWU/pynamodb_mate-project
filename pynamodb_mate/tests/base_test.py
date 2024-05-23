# -*- coding: utf-8 -*-

import typing as T
import moto
import botocore.exceptions
from boto_session_manager import BotoSesManager
from pynamodb.connection import Connection
from pynamodb.models import Model
from ..vendor import mock_aws
from .constants import BUCKET, AWS_PROFILE

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client


class BaseTest(mock_aws.BaseMockTest):
    """
    Base class for all test cases that requires a DynamoDB table. Make it easy
    to test both using mock and real Amazon DynamoDB table.
    """

    mock_list = [
        moto.mock_s3,
        moto.mock_dynamodb,
        moto.mock_sts,
    ]

    model_list = []  # Put all ``pynamodb.models.Model`` class you declared here
    conn: T.Optional[Connection] = None
    s3_client: T.Optional["S3Client"] = None

    @staticmethod
    def cleanup_connection(model_class: Model):
        """
        Clean up the cached Pynamodb connection object so that PynamoDB
        can find the right boto3 session.
        """
        if model_class._connection is not None:
            if model_class._connection.connection is not None:
                model_class._connection.connection = None
            model_class._connection = None

    @staticmethod
    def create_bucket(s3_client: "S3Client", bucket: str):
        try:
            s3_client.head_bucket(Bucket=BUCKET)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                s3_client.create_bucket(Bucket=BUCKET)
            else:
                raise e

    @classmethod
    def setup_class(cls):
        cls.setup_class_pre_hook()
        cls.setup_moto()

        # code below is for making sure pynamodb connection can find the right boto3 session
        # to use in mock mode or AWS mode. The pynamodb connection design is flawed,
        # we have to do some hacky things to make it work.
        for model_class in cls.model_list:
            cls.cleanup_connection(model_class)
            model_class.Meta.region = cls.region_name
        if cls.use_mock:
            cls.s3_client = cls.bsm.s3_client
            cls.create_bucket(cls.s3_client, BUCKET)
            cls.conn = Connection(region="us-east-1")
            for model_class in cls.model_list:
                model_class.create_table(wait=False)
        else:
            # create s3 bucket first, sometimes Model.delete_all() will fail if the bucket not exists
            cls.bsm = BotoSesManager(profile_name=AWS_PROFILE)
            with cls.bsm.awscli():
                cls.s3_client = cls.bsm.s3_client
                cls.create_bucket(cls.s3_client, BUCKET)
                cls.conn = Connection(region="us-east-1")
                _ = cls.conn.session.get_credentials()
                for model_class in cls.model_list:
                    model_class.create_table(wait=True)
                    model_class.delete_all()
        cls.setup_class_post_hook()
