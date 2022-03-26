from threading import Timer
from threading import Thread
from threading import Event


class RepeatTimer(Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()

    def cancel(self):
        self.finished.set()

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


g_setTimerObj = set()


def RegisterTick(_, nTickTime, CallBack, *tParam):
    TimerObj = RepeatTimer(nTickTime / 1000.0, CallBack, tParam)
    TimerObj.start()
    g_setTimerObj.add(TimerObj)
    return TimerObj


RegisterNotFixTick = RegisterTick


def RegisterOnceTick(_, nTickTime, CallBack, *tParam):
    TimerObj = Timer(nTickTime / 1000.0, CallBack, tParam)
    TimerObj.start()
    g_setTimerObj.add(TimerObj)
    return TimerObj


def UnRegisterTick(nTickID):
    if nTickID is None:
        return
    TimerObj = nTickID
    g_setTimerObj.discard(TimerObj)
    TimerObj.cancel()


def IsExistTickID(nTickID):
    if not nTickID:
        return False
    return nTickID in g_setTimerObj


if __name__ == '__main__':
    def f(a, b):
        print("f:", a, b)

    t1 = RegisterTick(None, 100, f, 1, 2)
    t2 = RegisterOnceTick(None, 450, UnRegisterTick, t1)
