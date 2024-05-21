# -*- coding: utf-8 -*-

import os
import sys
import pynamodb

PY_VER = f"{sys.version_info.major}{sys.version_info.minor}"
PYNAMODB_VER = pynamodb.__version__.replace(".", "_")
AWS_PROFILE = "bmt_app_dev_us_east_1"
BUCKET = "bmt-app-dev-us-east-1-data"
PREFIX = "projects/pynamodb_mate/unit-test/"
IS_CI = "CI" in os.environ
