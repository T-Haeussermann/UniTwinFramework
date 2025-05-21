import json
import time
from queue import Queue
from fastapi import APIRouter, BackgroundTasks
from .class_ComponentABC import Component
from .class_Event import Event

class class_SkillExecution(Component):
    def __init__(self, _conf):
        self._event = Event()
        self.Q = Queue()
        # self.sensor_data_old = {}
        self.active_skills = {}

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self._router = APIRouter()
        self.configure_router()

    def evaluate_measurement(self):
        msg = self.Q.get()
        print(msg)
        msg["Topic"] = msg["Topic"].replace(self.parent._uid + "/", "")
        print(msg["Topic"], msg["Message"])
        if msg["Topic"] == "Measurement":
            measurement = msg["Message"]
            sensor = measurement["sensor"]
            value = measurement["value"]


            # check if sensor is in configuration
            if sensor not in self.sensors_data:
                print(f"Sensor not found in sensor data. Please update {self._id}'s configuration.")
            else:
                # check if value exceeds upper bound
                if self.sensors_data[sensor]["bounds"]["upper"] < value:
                    skill = {"name": self.sensors_data[sensor]["skill"]["upper"]["name"], "method": self.sensors_data[sensor]["skill"]["upper"]["method"]}
                    if self.sensors_data[sensor]["skill"]["upper"]["params"] != {}:
                        skill["params"] = self.sensors_data[sensor]["skill"]["upper"]["params"]
                    skill = json.dumps(skill)
                    print(skill)
                    self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)
                    self.active_skills[sensor] = "upper"

                # check if value drops below lower bound
                elif self.sensors_data[sensor]["bounds"]["lower"] > value:
                    skill = {"name": self.sensors_data[sensor]["skill"]["lower"]["name"], "method": self.sensors_data[sensor]["skill"]["lower"]["method"]}
                    if self.sensors_data[sensor]["skill"]["lower"]["params"] != {}:
                        skill["params"] = self.sensors_data[sensor]["skill"]["lower"]["params"]
                    skill = json.dumps(skill)
                    print(skill)
                    self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)
                    self.active_skills[sensor] = "lower"

                # Check if value is back within bounds
                elif self.sensors_data[sensor]["bounds"]["lower"] <= value <= self.sensors_data[sensor]["bounds"]["upper"]:
                    if self.active_skills.get(sensor):
                        print(f"Sensor {sensor} back in bounds, stopping active skill.")
                        if self.active_skills[sensor] == "upper":
                            skill = {"name": self.sensors_data[sensor]["skill"]["upper"]["name"], "method": self.sensors_data[sensor]["skill"]["upper"]["end_method"]}
                            # if self.sensors_data[sensor]["skill"]["lower"]["params"] != {}:
                            #     skill["params"] = self.sensors_data[sensor]["skill"]["upper"]["params"]
                            skill = json.dumps(skill)
                            print(skill)
                            self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)

                            self.active_skills[sensor] = None  # Clear active skill state

                        if self.active_skills[sensor] == "lower":
                            skill = {"name": self.sensors_data[sensor]["skill"]["lower"]["name"], "method": self.sensors_data[sensor]["skill"]["lower"]["end_method"]}
                            # if self.sensors_data[sensor]["skill"]["lower"]["params"] != {}:
                            #     skill["params"] = self.sensors_data[sensor]["skill"]["lower"]["params"]
                            skill = json.dumps(skill)
                            print(skill)
                            self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)

                            self.active_skills[sensor] = None  # Clear active skill state

    def run(self):
        # get self.dbInstance from given name in config
        # self.dbInstance = self.parent.getChild(self.dbInstance)

        # get self.mqttInstance from given name in config
        self.mqttInstance = self.parent.getChild(self.mqttInstance)

    def last(self):
        # stop all active skills before removing
        print(self.active_skills)
        for sensor in self.active_skills:
            print(sensor)
            if self.active_skills[sensor] == "upper":
                skill = {"name": self.sensors_data[sensor]["skill"]["upper"]["name"],
                         "method": self.sensors_data[sensor]["skill"]["upper"]["end_method"]}
                skill = json.dumps(skill)
                print(skill)
                self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)
            if self.active_skills[sensor] == "lower":
                skill = {"name": self.sensors_data[sensor]["skill"]["lower"]["name"],
                         "method": self.sensors_data[sensor]["skill"]["lower"]["end_method"]}
                skill = json.dumps(skill)
                print(skill)
                self.mqttInstance.publish(f"{self.parent._uid}/skill", skill)



    def configure_router(self):
        @self._router.get(f"/{self._id}/dosomething")
        def do_somthing():
            pass
