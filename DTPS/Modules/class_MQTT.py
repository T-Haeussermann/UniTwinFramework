import json
import paho.mqtt.client as mqtt
from queue import Queue
from fastapi import APIRouter
from .class_ComponentABC import Component
from .class_Event import Event

class class_MQTT(Component):
    def __init__(self, _conf):
        self._event = Event()

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.Q = Queue()
        self._timeout = 60
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

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

    def configure_router(self):
        @self._router.get("/Test/{Topic}/{Payload}")
        def send_msg(Topic, Payload, Qos = 0):
            self.publish(Topic, Payload, Qos)
            return "Message published!"



