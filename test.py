# coding=utf-8
import unittest
from time import sleep

from memory_cache import MemoryCache


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
        for _ in xrange(100):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        for k in xrange(2, 101):
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
        for k in xrange(100):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误, 参数虽不同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")
            r = a(k)
            self.assertEqual((1, 2), r, u"结果有误, 参数虽不同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

    def test3(self):
        """0.1s过期，区分入参"""
        @MemoryCache(nLimitTimeMs=10)
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for _ in xrange(1, 101):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误, 参数相同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        sleep(0.01)
        for k in xrange(2, 101):
            r = a(1)
            self.assertEqual((1, 2), r, u"结果有误")
            self.assertEqual(k, ls[0], u"函数内部触发次数错误, 相隔的时间应每次都是新的结果")
            sleep(0.01)

    def test4(self):
        """0.1s过期，不区分入参"""
        @MemoryCache(nLimitTimeMs=10, bUniqueArg=False)
        def a(i, j=2):
            ls[0] += 1
            return i, j

        ls = [0]
        for k in xrange(1, 101):
            r = a(k)
            self.assertEqual((1, 2), r, u"结果有误, 参数相同, 应只缓存第一个结果")
            self.assertEqual(1, ls[0], u"函数内部触发次数错误")

        sleep(0.01)
        for k in xrange(2, 101):
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
        for _ in xrange(100):
            a1.a(1)
            a2.a(1)
            self.assertEqual(1, a1.m_nACall)
            self.assertEqual(1, a2.m_nACall)

            a1.b(1)
            a2.b(0)
            self.assertEqual(2, a1.s_nBCall)
            self.assertEqual(2, a2.s_nBCall)

        # 参数不相同，会重覆触发
        for j in xrange(2, 102):
            a1.a(j)
            a2.a(j)
            self.assertEqual(j, a1.m_nACall)
            self.assertEqual(j, a2.m_nACall)
            self.assertEqual(2*j, a1.m_nACall+a2.m_nACall)

            a1.b(j)
            a2.b(1000+j)
            self.assertEqual(2*j, a1.s_nBCall)
            self.assertEqual(2*j, a2.s_nBCall)
