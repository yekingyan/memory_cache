# coding=utf-8
import time
from functools import wraps


NEVER_EXPIRE = 0


class MemoryCache(object):
    def __init__(self, nLimitTimeMs=NEVER_EXPIRE, bUniqueArg=True):
        """
        根据入参缓存函数调用结果
        Args:
            nLimitTimeMs: 最小更新时间间隙, 默认只返回缓存
            bUniqueArg: 是否区分入参作为更新依据
        """
        self.instance = None
        self.m_nLimitTimeMs = nLimitTimeMs
        self.m_bUniqueArg = bUniqueArg

        self.arg2res = {}

    def __get__(self, instance, cls):
        self.instance = instance
        return self

    def _GetRes(self, key):
        result, nLastUpdateTs = self.arg2res.get(key, (None, None))
        return result, nLastUpdateTs

    def _IsExpired(self, key):
        _, nLastUpdateTs = self._GetRes(key)
        if nLastUpdateTs is None:
            return True
        if self.m_nLimitTimeMs == NEVER_EXPIRE:
            return False
        if (time.time() - nLastUpdateTs) * 1000 > self.m_nLimitTimeMs:
            return True
        return False

    def __call__(self, func):
        @wraps(func)
        def Wrapper(*args, **kwargs):
            key = str((args, kwargs)) if self.m_bUniqueArg else "simple"
            if not self._IsExpired(key):
                result, _ = self._GetRes(key)
                return result

            if self.instance is not None:
                res = func(self.instance, *args, **kwargs)
            else:
                res = func(*args, **kwargs)
            self.arg2res[key] = res, time.time()
            return res
        return Wrapper
