from .class_ComponentABC import Component
from .class_Event import Event
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.observers.polling import PollingObserver
from queue import Queue
from pathlib import Path
import requests


class class_Crawler(Component):
    def __init__(self, _conf):
        self._event = Event()
        self.Q = Queue()
        self.path = "./watch"
        self.filePath = ""

        for item in _conf:
            self.__setattr__(item, _conf[item])

        # create dir if not present
        self.createDir()
        self.documents = dict()  # key = document label   value = Document reference

        self.event_handler = LoggingEventHandler()   #FileSystemEventHandler()
        self.event_handler.on_any_event = self.on_any_event
        self.event_handler.on_created = self.on_created
        self.observer = PollingObserver() #Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=False)

    def run(self):
        print(self._parent)
        resp = requests.get("http://dtps-svc.dt.svc.cluster.local:8000/mount/" + self._parent._uid + "/?path=" + self._dir)
        self.observer.start()
    def createDir(self):
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def on_any_event(self, event):
        print(event.src_path, event.event_type)

    def on_created(self, event):
        print("created: " + event.src_path)
        if "swp" not in event.src_path:
            if hasattr(self, "_subscribers"):
                for subscriber in self._subscribers:
                    subscriber = self.parent.getChild(subscriber)
                    subscriber.Q.put(event.src_path)
            self._event()

