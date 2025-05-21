from queue import Queue
import traceback
from Modules.class_ComponentABC import Component
from .class_Event import Event

class method_MQTT(Component):
    def __init__(self, _conf):
        self._subscribers = {}
        self._event = Event()
        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.parent = ""
        self.Q = Queue()
    def method_MQTT(self):
        msg = self.Q.get()
        msg["Topic"] = msg["Topic"].replace(self.parent._uid + "/", "")

        if msg["Topic"] == "Measurement":
            print(msg)
            for sensor in msg["Message"]:
                try:
                    value = float(msg["Message"][sensor]["value"])
                    if isinstance(value, bool):
                        if value == True:
                            value = 1.0
                        else:
                            value = 0.0
                    if "unit" in msg["Message"][sensor]:
                        unit = msg["Message"][sensor]["unit"]
                        if unit == "":
                            unit = None
                    else:
                        unit = None
                    # db = self.parent.getChild("class_Influxdb-I1")
                    # db.write(self.parent._uid, sensor, value, unit)

                    if hasattr(self, "_subscribers"):
                        for subscriber in self._subscribers:
                            subscriber = self.parent.getChild(subscriber)
                            subscriber.Q.put({"Topic": msg["Topic"], "Message":{"sensor": sensor, "value": value, "unit": unit}})
                    self._event()

                except Exception as e:
                    traceback.print_exc()
                    print("Invalid Format")

        elif msg["Topic"] == "Topic1":
            print("Oh its a message in Topic1, I'll do somthing with it")
        elif msg["Topic"] == "Topic2":
            print("Oh its a message in Topic2, I'll do somthing with it")
        elif msg["Topic"] == "Topic3":
            print("Oh its a message in Topic3, I'll do somthing with it")
        elif msg["Topic"] == "Topic4":
            print("Oh its a message in Topic4, I'll do somthing with it")