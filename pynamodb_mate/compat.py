# -*- coding: utf-8 -*-

import sys

if (
    sys.version_info.major == 2
    or (sys.version_info.major == 3 and sys.version_info.minor < 6)
):
    raise NotImplementedError("we don't support < Python3.6!")

if sys.version_info.minor < 8:
    from cached_property import cached_property
else:
    from functools import cached_property
