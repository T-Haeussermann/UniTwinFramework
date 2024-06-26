import json
import requests
from queue import Queue
from fastapi import APIRouter
from .class_ComponentABC import Component
from .class_Event import Event


class class_serverMeasurements(Component):
    def __init__(self, _conf):
        self._event = Event()

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.sensor_data = {}

        self.Q = Queue()

    def set_measurement_values(self):
        msg = self.Q.get()
        msg["Topic"] = msg["Topic"].replace(self.parent._uid + "/", "")

        if msg["Topic"] == "Measurement":
            for sensor in msg["Message"]:
                self.sensor_data[sensor] = msg["Message"][sensor]

            if hasattr(self, "_mqtt_subscribers"):
                mqtt_client = self.parent.getChild("class_MQTT-I1")
                payload = {"_id": self.parent._uid, "measurement": self.sensor_data}
                if mqtt_client != None:
                    for _mqtt_subscriber in self._mqtt_subscribers:
                        mqtt_client.publish(self._mqtt_subscribers[_mqtt_subscriber], json.dumps(payload))

            if hasattr(self, "_http_subscribers"):
                for _http_subscriber in self._http_subscribers:
                    requests.post(self._http_subscribers[_http_subscriber], data=self.sensor_data)

    def configure_router(self):
        @self._router.get("/sensor_data/")
        def get_sensor_data(sensor: str = "", all_sensors: bool = False):
            if sensor == "":
                all_sensors = True
            if self.sensor_data != {}:
                if all_sensors == True:
                    return self.sensor_data
                elif all_sensors == False:
                    if sensor in self.sensor_data:
                        return self.sensor_data[sensor]
                    else:
                        return {"msg": "sensor not found"}
            else:
                return {"msg": "no sensor_data found"}

        @self._router.get("/sensors/")
        def get_sensors():
            sensor_list = []
            for sensor in self.sensor_data:
                sensor_list.append(sensor)
            return sensor_list