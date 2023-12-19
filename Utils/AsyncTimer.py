import time

__all__ = ['AsyncTimer']

class AsyncTimer:
    # ContextManager to record real time(ns) of the execution of a coroutine
    def __init__(self, start_time: int):
        self.start_time = start_time

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.time = time.time_ns() - self.start_time

