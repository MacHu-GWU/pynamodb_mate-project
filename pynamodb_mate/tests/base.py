# -*- coding: utf-8 -*-

import moto
from pynamodb.connection import Connection


class BaseTest:
    mock_s3 = None
    mock_dynamodb = None

    @classmethod
    def mock_start(cls):
        cls.mock_s3 = moto.mock_s3()
        cls.mock_dynamodb = moto.mock_dynamodb()

        cls.mock_s3.start()
        cls.mock_dynamodb.start()

        Connection()

    @classmethod
    def mock_stop(cls):
        cls.mock_s3.stop()
        cls.mock_dynamodb.stop()

    @classmethod
    def setup_class(cls):
        cls.mock_start()

    @classmethod
    def teardown_class(cls):
        cls.mock_stop()
