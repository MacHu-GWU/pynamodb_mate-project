# -*- coding: utf-8 -*-

import sys
from .helper import run_cov_test
from .base import BaseTest

py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
BUCKET_NAME = "aws-data-lab-sanhe-for-everything"
