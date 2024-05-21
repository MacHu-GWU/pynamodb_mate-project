# -*- coding: utf-8 -*-

import warnings
from .decorator import decorator


@decorator
def mark_pending_deprecation(func, _msg: str, *args, **kwargs):
    """
    这个不是给最终用户看的, 这个是给开发者自己看的.
    """
    warnings.warn(
        f"{func.__name__} will be deprecated soon. {_msg}",
        PendingDeprecationWarning,
    )
    result = func(*args, **kwargs)
    return result


@decorator
def mark_deprecation(func, _msg: str, *args, **kwargs):
    """
    这是给最终用户看的, 提示用户使用新的 API.
    """
    warnings.warn(
        f"{func.__name__} is deprecated. {_msg}",
        DeprecationWarning,
    )
    result = func(*args, **kwargs)
    return result
