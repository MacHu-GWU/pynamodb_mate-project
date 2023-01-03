# -*- coding: utf-8 -*-

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)
