# -*- coding: utf-8 -*-

import os
import sys
import pynamodb

py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
pynamodb_ver = pynamodb.__version__.replace(".", "_")
aws_profile = "bmt_app_dev_us_east_1"
bucket = "bmt-app-dev-us-east-1-data"
prefix = "projects/pynamodb_mate/"
is_ci = "CI" in os.environ
