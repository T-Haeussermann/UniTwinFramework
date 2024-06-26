from .class_ComponentABC import Component
from .class_Event import Event
from queue import Queue
import pathlib


class class_DataProcessing(Component):
    def __init__(self, _conf):
        self._event = Event()
        self.Q = Queue()

        for item in _conf:
            self.__setattr__(item, _conf[item])

    def process(self):
        path = self.Q.get()
        datatype = pathlib.Path(path).suffix
        print(f"Oh its a file of type {datatype}")



