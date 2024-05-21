# -*- coding: utf-8 -*-

import moto
from ..vendor import mock_aws


class BaseTest(mock_aws.BaseMockTest):
    mock_list = [
        moto.mock_s3,
        moto.mock_dynamodb,
        moto.mock_sts,
    ]
