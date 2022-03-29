# coding=utf-8
import gc
import cProfile
import pstats
from datetime import datetime
from functools import wraps


class CheckRuntime(object):
    """检查运行时长"""
    def __init__(self, szName, bGc=True):
        self.m_szName = szName
        self.m_bGc = bGc

    def __enter__(self):
        if self.m_bGc:
            gc.collect()
        self.m_dtStart = datetime.now()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        dtElapsed = datetime.now() - self.m_dtStart
        print("** Test {} took {} **".format(self.m_szName, dtElapsed))


def DoFuncCprofile(szFilename=None, bGc=True, szSortby="cumtime", nLine=10):
    """性能分析装饰器"""
    def Wrapper(func):
        @wraps(func)
        def ProfiledFunc(*args, **kwargs):
            if bGc:
                gc.collect()

            Profile = cProfile.Profile()
            Profile.enable()
            result = func(*args, **kwargs)
            Profile.disable()

            Ps = pstats.Stats(Profile)
            Ps.sort_stats(szSortby)
            Ps.print_stats(nLine)

            if szFilename is not None:
                Ps.dump_stats(szFilename)
            return result

        Wrapper.func_closure_for_reload = func
        return ProfiledFunc

    return Wrapper


"""
# 检查运行时长
with CheckRuntime("title"):
    m()


# profile
## 开始profile
import gac_gas.debug_watch as w
w.DoFuncCprofile(szFilename="a.prof", nLine=5)(self.UpdateRewardPreListView)(True)

## 出分析图
>>>gprof2dot -f pstats a.prof | dot -Tpng -o output.png
"""
