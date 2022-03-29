# coding=utf-8
import time
from functools import wraps
from collections import OrderedDict


NEVER_EXPIRE = 0


class LRUCache(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def put(self, key, value):
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

    def get(self, key, default=None):
        if key not in self.cache:
            return default
        value = self.cache.pop(key)
        self.put(key, value)
        return value

    def __setitem__(self, key, value):
        self.put(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in self.cache


class FuncAttr(object):
    def __init__(self, nExpireMs=NEVER_EXPIRE, bUniqueArg=True):

        self.m_InstanceObj = None
        self.m_nExpireMs = nExpireMs
        self.m_bUniqueArg = bUniqueArg

        self.dictArg2res = {}

    def __get__(self, instance, cls):
        self.m_InstanceObj = instance
        return self

    def _GetRes(self, key):
        result, nCacheExpireTs = self.dictArg2res.get(key, (None, None))
        return result, nCacheExpireTs

    def _IsExpired(self, key=None, nCacheExpireTs=None):
        if nCacheExpireTs is None:
            _, nCacheExpireTs = self._GetRes(key)
        if nCacheExpireTs is None:
            return True
        if self.m_nExpireMs == NEVER_EXPIRE:
            return False
        assert isinstance(nCacheExpireTs, (int, float))
        return time.time() >= nCacheExpireTs

    def MakeKey(self, args, kwargs):
        if not self.m_bUniqueArg:
            return "simple"
        key = args
        if kwargs:
            for item in kwargs.iteritems():
                key += item
        return key


class MemoryCache(FuncAttr):
    """
    函数缓存装饰器
    """

    def __init__(self, nExpireMs=NEVER_EXPIRE, bUniqueArg=True, nSize=1024):
        super(MemoryCache, self).__init__(nExpireMs, bUniqueArg)
        self.dictArg2res = LRUCache(nSize)

    def __call__(self, func):
        @wraps(func)
        def Wrapper(*args, **kwargs):
            key = self.MakeKey(args, kwargs)
            result, nCacheExpireTs = self._GetRes(key)
            if not self._IsExpired(nCacheExpireTs=nCacheExpireTs):
                return result

            if self.m_InstanceObj is not None:
                res = func(self.m_InstanceObj, *args, **kwargs)
            else:
                res = func(*args, **kwargs)
            self.dictArg2res[key] = res, time.time() + self.m_nExpireMs / 1000.0
            return res
        return Wrapper


class DelayRun(FuncAttr):
    """
    延迟调用装饰器
    """
    def __init__(self, nDelayMs=1000, bUniqueArg=True, TickEngine=None):
        assert nDelayMs > 0
        super(DelayRun, self).__init__(nDelayMs, bUniqueArg)
        self.m_TickEngine = TickEngine

    def __call__(self, func):
        @wraps(func)
        def Wrapper(*args, **kwargs):
            key = self.MakeKey(args, kwargs)
            nTickID, nCacheExpireTs = self._GetRes(key)
            if not self._IsExpired(key, nCacheExpireTs=nCacheExpireTs) and self.m_TickEngine.IsExistTickID(nTickID):
                return nTickID

            RegisterOnceTick = self.m_TickEngine.RegisterOnceTick
            if self.m_InstanceObj is not None:
                nTickID = RegisterOnceTick("", self.m_nExpireMs, func, self.m_InstanceObj, *args, **kwargs)
            else:
                nTickID = RegisterOnceTick("", self.m_nExpireMs, func, *args, **kwargs)
            self.dictArg2res[key] = nTickID, time.time() + self.m_nExpireMs / 1000.0
            return nTickID
        return Wrapper
