import json
import time
from queue import Queue
import numpy as np
import scipy
import statsmodels.api as sm
import matplotlib
import matplotlib.pyplot as plt
from threading import Thread
from joblib import dump, load
import traceback
from fastapi import APIRouter, BackgroundTasks
from .class_ComponentABC import Component
from .class_Event import Event

class class_TSDanalyse(Component):
    def __init__(self, _conf):
        self._event = Event()
        self.Q = Queue()
        self.initialized = False
        self.data = None
        self.sensors = None
        self.sensorBounds = {}
        self.sensorData = {}
        self.sensorStates = {}

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        # get self.dbInstance from given name in config
        # self.dbInstance = self.parent.getChild(self.dbInstance)

    def getData(self, initialization_time):
        # Load the time series data
        self.data = self.dbInstance.query(self.parent._uid, "data_frame", initialization_time, False)

        # get list of different sensors
        self.sensors = sorted(list(set(self.data["Sensor"].to_list())))

        # selecting rows based on condition and create sensordata from it
        for sensor in self.sensors:
            sensor_df = self.data[self.data['Sensor'] == sensor]
            self.sensorData[sensor] = {"data": ""}
            self.sensorData[sensor]["data"] = sensor_df['Value'][-100:].reset_index(drop=True)


    def evaluate(self):
        if self.initialized == True:
            sensor_data = self.Q.get()
            sensor = sensor_data["Sensor"]
            value = sensor_data["Value"]
            print(f"lower bound: {self.sensorBounds[sensor]['lower_bound']} and upper bound: {self.sensorBounds[sensor]['upper_bound']} and value: {value}")
            old_sensor_state = self.sensorStates[sensor]

            if value >= self.sensorBounds[sensor]['lower_bound'] and  value <= self.sensorBounds[sensor]['upper_bound']:
                print(f"Measurement from sensor {sensor} in range.")
                self.sensorStates[sensor] = "ok"
                action = "stop"
                state = old_sensor_state

            elif value <= self.sensorBounds[sensor]['lower_bound']:
                print(f"Measurement from sensor {sensor} too low.")
                self.sensorStates[sensor] = "too low"
                state = self.sensorStates[sensor]
                action = "start"
            elif value >= self.sensorBounds[sensor]['upper_bound']:
                print(f"Measurement from sensor {sensor} too high.")
                self.sensorStates[sensor] = "too high"
                state = self.sensorStates[sensor]
                action = "start"

            if old_sensor_state != self.sensorStates[sensor]:
                if old_sensor_state == "ok" and self.sensorStates[sensor] == "too low" or old_sensor_state == "ok" and self.sensorStates[sensor] == "too high":
                    # Send Message to activate actions
                    msg = json.dumps({sensor: {"state": state, "action": action}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                elif old_sensor_state == "too low" and self.sensorStates[sensor] == "ok" or old_sensor_state == "too high" and self.sensorStates[sensor] == "ok":
                    # Send Message to activate actions
                    msg = json.dumps({sensor: {"state": state, "action": action}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                elif old_sensor_state == "too low" and self.sensorStates[sensor] == "too high":
                    # Send Message to activate actions
                    msg = json.dumps({sensor: {"state": "too low", "action": "stop"}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                    msg = json.dumps({sensor: {"state": state, "action": action}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                elif old_sensor_state == "too high" and self.sensorStates[sensor] == "too low":
                    # Send Message to activate actions
                    msg = json.dumps({sensor: {"state": "too high", "action": "stop"}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                    msg = json.dumps({sensor: {"state": state, "action": action}})
                    print(msg)
                    self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
        else:
            self.Q.queue.clear()

    def initialize(self, initialization_time):
        # Send Message to stop all actions if already initialized
        if self.sensors != None:
            for sensor in self.sensors:
                msg = json.dumps({sensor: {"state": "too low", "action": "stop"}})
                self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                msg = json.dumps({sensor: {"state": "too high", "action": "stop"}})
                self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)

        # Wait for the initialization_time to pass and extract data
        time.sleep(initialization_time)
        self.getData(initialization_time)

        # calculate average and standard deviation for every sensor, set bound and states
        for sensor in self.sensors:
            average_value = self.sensorData[sensor]['data'].mean()
            std_deviation = self.sensorData[sensor]['data'].std()
            lower_bound = round(average_value - 2 * std_deviation, 2)
            upper_bound = round(average_value + 2 * std_deviation, 2)
            self.sensorBounds[sensor] = {"lower_bound": lower_bound, "upper_bound": upper_bound}
            self.sensorStates[sensor] = "ok"

        # completing initialization by setting initialized to True
        self.initialized = True



    def setBounds(self, description):
        # Send Message to stop all actions if already initialized
        print(self.sensors)
        if self.sensors != None:
            for sensor in self.sensors:
                msg = json.dumps({sensor: {"state": "too low", "action": "stop"}})
                self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)
                msg = json.dumps({sensor: {"state": "too high", "action": "stop"}})
                self.mqttInstance.publish(self.parent._uid + "/actions", msg, Qos=2)

        # get list of different sensors
        self.sensors = sorted(list(set(description)))

        # set bound and states
        try:
            for sensor in description:
                lower_bound = description[sensor]["lower_bound"]
                upper_bound = description[sensor]["upper_bound"]
                self.sensorBounds[sensor] = {"lower_bound": lower_bound, "upper_bound": upper_bound}
                self.sensorStates[sensor] = "ok"

            self.initialized = True
        except Exception as e:
            traceback.print_exc()

    def run(self):
        # get self.dbInstance from given name in config
        self.dbInstance = self.parent.getChild(self.dbInstance)

        # get self.mqttInstance from given name in config
        self.mqttInstance = self.parent.getChild(self.mqttInstance)

    def configure_router(self):
        @self._router.get("/TSDanalyse/initialize")
        def read_item(background_tasks: BackgroundTasks, initialization_time: int = None, description: str = None, overwrite: bool = False):
            if self.initialized is True and overwrite is True:
                if description != None and initialization_time != None:
                    return {"Status": "Error! Please provide initialization_time or description."}
                elif description != None:
                    description = json.loads(description)
                    background_tasks.add_task(self.setBounds, description)
                    return {"Status": "Initializing..."}
                elif initialization_time != None:
                    background_tasks.add_task(self.initialize, initialization_time)
                    return {"Status": "Initializing..."}
            elif self.initialized is False:
                if description != None and initialization_time != None:
                    return {"Status": "Error! Please provide initialization_time or description."}
                elif description != None:
                    description = json.loads(description)
                    background_tasks.add_task(self.setBounds, description)
                    return {"Status": "Initializing..."}
                elif initialization_time != None:
                    background_tasks.add_task(self.initialize, initialization_time)
                    return {"Status": "Initializing..."}
                return {"Status": "Initializing..."}
            elif self.initialized is True and overwrite is False:
                return {"Status": "Already initialized. Doing nothing. Set overwrite to true to reinitialize."}
            return {"self.initialized": self.initialized, "overwrite": overwrite}
