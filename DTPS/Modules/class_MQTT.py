import json
import paho.mqtt.client as mqtt
from queue import Queue
from fastapi import APIRouter
from datetime import datetime
import time
import threading
from .class_ComponentABC import Component
from .class_Event import Event

class class_MQTT(Component):
    def __init__(self, _conf):
        self._event = Event()

        self.Q = Queue()
        self._timeout = 60
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        self.first = True
        self.t_start = None
        self.count_msg = 0
        self.timer_done = False  # Flag to ensure we write once after 60 seconds

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self._router = APIRouter()
        self.configure_router()

    def on_connect(self, client, userdata, flags, rc, properties):
        print("Connected with result code " + str(rc))
        for item in self._topic_sub:
            self.client.subscribe(self.parent._uid + "/" + item)
        # self.client.subscribe(self._topic_sub)

    def publish(self, Topic, Payload, Qos=0):
        Qos = int(Qos)
        self.client.publish(topic=Topic, payload=Payload, qos=Qos)
        # print("Message published")

    def on_message(self, client, userdata, msg):
        # logic for evaluation paper

        # Synchronization Latency
        # self.publish("TEST", "received")
        # Synchronization Latency

        # logic for evaluation paper
        """implement pass message to class based on topic"""
        Topic = msg.topic
        """erro handling for non JSON messages"""
        try:
            Message = json.loads(msg.payload.decode("utf-8"))
        except:
            Message = msg.payload.decode("utf-8")
        if hasattr(self, "_subscribers"):
            for subscriber in self._subscribers:
                subscriber = self.parent.getChild(subscriber)
                subscriber.Q.put({"Topic": Topic, "Message": Message})

        # logic for evaluation paper

        # Data throughput
        # If first message, record the start time
        # if self.first:
        #     self.t_start = time.time()
        #     self.first = False
        #
        # self.count_msg = self.count_msg + 1

        # Check if 60 seconds have passed and file hasn't been written yet
        # if not self.timer_done and (time.time() - self.t_start) >= 60:
        #     # Write the count_msg to file (convert to string)
        #     with open("result.txt", "w") as f:
        #         f.write(str(self.count_msg))
        #     self.publish("Msg_Count", str(self.count_msg))
        #     self.timer_done = True
        # Data throughput

        # logic for evaluation paper
        self._event()

    # def on_message(self, client, userdata, msg):
    #     # logic for evaluation paper
    #
    #     # Synchronization Latency
    #     # self.publish("TEST", "received")
    #     # Synchronization Latency
    #
    #     # logic for evaluation paper
    #
    #     # Data throughput
    #     # If first message, record the start time
    #     if self.first:
    #         self.t_start = time.time()
    #         self.first = False
    #
    #     self.count_msg = self.count_msg + 1
    #
    #     # Check if 60 seconds have passed and file hasn't been written yet
    #     if not self.timer_done and (time.time() - self.t_start) >= 60:
    #         # Write the count_msg to file (convert to string)
    #         with open("result.txt", "w") as f:
    #             f.write(str(self.count_msg))
    #         self.publish("Msg_Count", str(self.count_msg))
    #         self.timer_done = True
    #     # Data throughput
    #
    #     # logic for evaluation paper
    #
    #     """ Asynchronously process the message in a separate thread to avoid blocking """
    #     thread = threading.Thread(target=self._process_message, args=(msg,))
    #     thread.start()

    def _process_message(self, msg):
        # This method is run in a separate thread for each message

        Topic = msg.topic
        try:
            Message = json.loads(msg.payload.decode("utf-8"))
        except:
            Message = msg.payload.decode("utf-8")

        if hasattr(self, "_subscribers"):
            for subscriber in self._subscribers:
                subscriber = self.parent.getChild(subscriber)
                subscriber.Q.put({"Topic": Topic, "Message": Message})

        self._event()

    def run(self):
        self.client.username_pw_set(self._username, self._passwd)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self._host, self._port, self._timeout)
        self.client.loop_start()
        #self.client.loop_forever()
        #self.client.loop_stop()

    def operation(self) -> str:
        return self._id

    def last(self):
        self.client.loop_stop()
        self.client.disconnect()

    def configure_router(self):
        @self._router.get(f"/{self._id}/publish")
        def send_msg(Topic, Payload, Qos = 0):
            self.publish(Topic, Payload, Qos)
            return "Message published!"



