import os
from fastapi import APIRouter, BackgroundTasks
from .class_ComponentABC import Component
from .class_Event import Event
from queue import Queue
import schedule
import datetime
import csv
import traceback

class class_TSexport(Component):
    def __init__(self, _conf):
        self._event = Event()
        self.Q = Queue()
        self.threading = True
        self.dir = "/UniTwin/export"
        self.export = False

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self._router = APIRouter()
        self.configure_router()


    def exportCSV(self):
        if self.export == True:
            db = self.parent.getChild(self.dbInstance)
            try:
                data = db.query(self.parent._uid, format="csv", time=self.frequence)
                rowcount = 0
                for row in data:
                    rowcount = rowcount + 1
                if rowcount > 0:
                    filename = f"{self.parent._uid}_{str(datetime.datetime.now())}.csv"
                    filename = filename.replace(" ", "_").replace(":", "-")
                    filepath = f"{self.dir}/{filename}"
                    with open(filepath, "w") as file:
                        writer = csv.writer(file)
                        for row in data:
                            writer.writerow(row)
                    if hasattr(self, "_subscribers"):
                        for subscriber in self._subscribers:
                            subscriber = self.parent.getChild(subscriber)
                            subscriber.Q.put(filepath)
                    self._event()
            except Exception as e:
                traceback.print_exc()
                print("Could not query any data from time series database!")

    def exportCSVmanual(self, timeSeconds):
        db = self.parent.getChild(self.dbInstance)
        try:
            data = db.query(self.parent._uid, format="csv", time=timeSeconds)
            rowcount = 0
            for row in data:
                rowcount = rowcount + 1
            if rowcount > 0:
                filename = f"{self.parent._uid}_{str(datetime.datetime.now())}.csv"
                filename = filename.replace(" ", "_").replace(":", "-")
                filepath = f"{self.dir}/{filename}"
                with open(filepath, "w") as file:
                    writer = csv.writer(file)
                    for row in data:
                        writer.writerow(row)
                if hasattr(self, "_subscribers"):
                    for subscriber in self._subscribers:
                        subscriber = self.parent.getChild(subscriber)
                        subscriber.Q.put(filepath)
                self._event()
                return f"Exportet csv file {filename}!"
        except Exception as e:
            traceback.print_exc()
            return "Could not query any data from time series database!"

    def cleanUP(self):
        for file in os.listdir(self.dir):
            os.remove(f"{self.dir}/{file}")

    def run(self):
        print(self)
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        schedule.every(self.frequence).seconds.do(self.exportCSV)
        while True:
            schedule.run_pending()

    def configure_router(self):
        @self._router.get(f"/{self._id}/TSDexport/getExport")
        def getExport():
            return self.export

        @self._router.post(f"/{self._id}/TSDexport/setExport/{value}")
        def setExport(value: bool = False):
            self.export = value
            return {self.export: f"Set to {str(value)}"}

        @self._router.get(f"/{self._id}/TSDexport/export")
        def getExport(timeSeconds: int = 30):
            return self.exportCSVmanual(timeSeconds)
