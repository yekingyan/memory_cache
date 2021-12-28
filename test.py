# coding=utf-8
import unittest
from time import sleep

from memory_cache import MemoryCache
from memory_cache import DelayRun
import tick_mgr


class TestMemoryCache(unittest.TestCase):
    def testArg(self):
        """测试参数传递"""
        @MemoryCache()
        def a(i, j=2):
            return i, j

        r = a(1)
        self.assertEqual((1, 2), r, u"结果有误")

        r = a(11, 22)
        self.assertEqual((11, 22), r, u"结果有误")

        r = a(11, j=222)
        self.assertEqual((11, 222), r, u"结果有误")

    def test1(self):
        """永不过期，区分入参"""
        @MemoryCache()
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for _ in range(100):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        for k in range(2, 101):
            r = a(k)
            self.assertEqual((k, 2), r, u"结果有误")
            self.assertEqual(k, ls[0], u"函数内部触发次数错误")

    def test2(self):
        """永不过期，不区分入参"""
        @MemoryCache(bUniqueArg=False)
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for k in range(100):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误, 参数虽不同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")
            r = a(k)
            self.assertEqual((1, 2), r, u"结果有误, 参数虽不同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

    def test3(self):
        """0.1s过期，区分入参"""
        @MemoryCache(nExpireMs=10)
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for _ in range(1, 101):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误, 参数相同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        sleep(0.01)
        for k in range(2, 10):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误")
            self.assertEqual(k, ls[0], u"函数内部触发次数错误, 相隔的时间应每次都是新的结果")
            sleep(0.01)

    def test4(self):
        """0.1s过期，不区分入参"""
        @MemoryCache(nExpireMs=10, bUniqueArg=False)
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for k in range(1, 101):
            r = a(k)
            self.assertEqual((1, 2), r, u"结果有误, 参数相同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        sleep(0.01)
        for k in range(2, 10):
            r = a(k)
            self.assertEqual((k, 2), r, u"结果有误")
            self.assertEqual(k, ls[0], u"函数内部触发次数错误, 相隔的时间应每次都是新的结果")
            sleep(0.01)

    def test5(self):
        """类中的方法"""
        class A(object):
            s_nBCall = 0

            def __init__(self):
                self.m_nACall = 0

            @MemoryCache()
            def a(self, i):
                self.m_nACall += 1
                return i

            @classmethod
            @MemoryCache()
            def b(cls, i):
                cls.s_nBCall += 1
                return i

        a1 = A()
        a2 = A()

        # 实例方法是互不影响的
        a1.a(1)
        self.assertEqual(1, a1.m_nACall)
        self.assertEqual(0, a2.m_nACall)
        a2.a(1)
        self.assertEqual(1, a1.m_nACall)
        self.assertEqual(1, a2.m_nACall)

        # 类方法共用
        a1.b(0)
        self.assertEqual(1, a1.s_nBCall)
        self.assertEqual(1, a2.s_nBCall)
        a2.b(1)
        self.assertEqual(2, a1.s_nBCall)
        self.assertEqual(2, a2.s_nBCall)

        # 参数相同，不会重覆触发
        for _ in range(100):
            a1.a(1)
            a2.a(1)
            self.assertEqual(1, a1.m_nACall)
            self.assertEqual(1, a2.m_nACall)

            a1.b(1)
            a2.b(0)
            self.assertEqual(2, a1.s_nBCall)
            self.assertEqual(2, a2.s_nBCall)

        # 参数不相同，会重覆触发
        for j in range(2, 102):
            a1.a(j)
            a2.a(j)
            self.assertEqual(j, a1.m_nACall)
            self.assertEqual(j, a2.m_nACall)
            self.assertEqual(2*j, a1.m_nACall+a2.m_nACall)

            a1.b(j)
            a2.b(1000+j)
            self.assertEqual(2*j, a1.s_nBCall)
            self.assertEqual(2*j, a2.s_nBCall)


def DelayRunTest(nDelayMs=0, bUniqueArg=True):
    return DelayRun(nDelayMs=nDelayMs, bUniqueArg=bUniqueArg, TickEngine=tick_mgr)


class TestDelayRun(unittest.TestCase):

    def test1(self):
        """延迟执行。区分入参, 根据入参间隔时间内只执行一次"""
        @DelayRunTest(nDelayMs=10)
        def f1(a):
            listF1RunTimes[0] += 1
            return a

        listF1RunTimes = [0]
        setTick = set()

        for i in range(100):
            nTickID = f1(1)
            setTick.add(nTickID)
        self.assertEqual(1, len(setTick))

        sleep(0.05)
        self.assertEqual(1, listF1RunTimes[0])

        for i in range(100):
            nTickID = f1(1)
            setTick.add(nTickID)
        self.assertEqual(2, len(setTick))

        sleep(0.05)
        self.assertEqual(2, listF1RunTimes[0])

        for i in range(100, 110):
            nTickID = f1(i)
            setTick.add(nTickID)
        self.assertEqual(12, len(setTick))

        sleep(0.05)
        self.assertEqual(12, listF1RunTimes[0])

    def test2(self):
        """延迟执行。不区分入参, 间隔时间内只执行一次"""

        @DelayRunTest(nDelayMs=10, bUniqueArg=False)
        def f1(a):
            listF1RunTimes[0] += 1
            return a

        listF1RunTimes = [0]
        setTick = set()

        for i in range(10):
            nTickID = f1(1)
            setTick.add(nTickID)
        self.assertEqual(1, len(setTick))

        sleep(0.05)
        self.assertEqual(1, listF1RunTimes[0])

        for i in range(10, 20):
            nTickID = f1(i)
            setTick.add(nTickID)
        self.assertEqual(2, len(setTick))

        sleep(0.05)
        self.assertEqual(2, listF1RunTimes[0])

    def testUnRegister(self):
        @DelayRunTest(nDelayMs=10)
        def f1(a):
            listF1RunTimes[0] += 1
            return a

        listF1RunTimes = [0]

        nTickID = list(map(lambda i: f1(1), range(100)))[0]
        tick_mgr.UnRegisterTick(nTickID)
        sleep(0.05)
        self.assertEqual(0, listF1RunTimes[0])

        nTickID = list(map(lambda i: f1(1), range(100)))[0]
        tick_mgr.UnRegisterTick(nTickID)
        sleep(0.05)
        self.assertEqual(0, listF1RunTimes[0])

        list(map(lambda i: f1(1), range(100)))
        sleep(0.05)
        self.assertEqual(1, listF1RunTimes[0])

        list(map(lambda i: f1(1), range(100)))
        sleep(0.05)
        self.assertEqual(2, listF1RunTimes[0])
