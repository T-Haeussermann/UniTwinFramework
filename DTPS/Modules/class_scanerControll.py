import json
import requests
from queue import Queue
from fastapi import APIRouter
from .class_ComponentABC import Component
from .class_Event import Event


class class_scanerControll(Component):
    def __init__(self, _conf):
        self._event = Event()

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.Q = Queue()

    def get_action(self):
        msg = self.Q.get()
        topic = msg["Topic"].replace(self.parent._uid + "/", "")
        message = msg["Message"]

        if topic == "Action":
            if message == "start_scan":
                method = "POST"
                endpoint = "/start_scan"
            elif message == "stop_scan":
                method = "POST"
                endpoint = "/stop_scan"
            elif message == "reset_scan":
                method = "POST"
                endpoint = "/reset_scan"
            elif message == "get_status":
                method = "GET"
                endpoint = "/lsc/get_status"
            elif message == "get_position":
                method = "GET"
                endpoint = "/lsc/get_position"
            elif message == "set_do_ref":
                method = "POST"
                endpoint = "/lsc/set_do_ref"
            elif message == "get_ham_status":
                method = "GET"
                endpoint = "/ham/get_ham_status"

            self.scanner_action(method, endpoint)

    def scanner_action(self, method, endpoint):
        if method == "GET":
            resp = str(requests.get(self._url + endpoint))
            print(resp)
            return resp

        if method == "POST":
            resp = str(requests.post(self._url + endpoint))
            print(resp)
            return resp

    def publish_actions(self, action):
        if hasattr(self, "_mqtt_subscribers"):
            mqtt_client = self.parent.getChild("class_MQTT-I1")
            payload = {"_id": self.parent._uid, "action": action}
            if mqtt_client != None:
                for _mqtt_subscriber in self._mqtt_subscribers:
                    mqtt_client.publish(self._mqtt_subscribers[_mqtt_subscriber], json.dumps(payload))

        if hasattr(self, "_http_subscribers"):
            for _http_subscriber in self._http_subscribers:
                requests.post(self._http_subscribers[_http_subscriber], data=action)


    def configure_router(self):
        @self._router.post("/start/")
        def start_scanner():
            method = "POST"
            endpoint = "/start_scan"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/stop/")
        def stop_scanner():
            method = "POST"
            endpoint = "/stop_scan"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/reset/")
        def reset_scanner():
            method = "POST"
            endpoint = "/reset_scan"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/lsc/get_status")
        def reset_scanner():
            method = "GET"
            endpoint = "/lsc/get_status"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/lsc/get_position")
        def reset_scanner():
            method = "GET"
            endpoint = "/lsc/get_position"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/lsc/set_do_ref")
        def reset_scanner():
            method = "POST"
            endpoint = "/lsc/set_do_ref"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/ham/get_ham_status")
        def reset_scanner():
            method = "GET"
            endpoint = "/ham/get_ham_status"
            resp = self.scanner_action(method, endpoint)
            return resp

        @self._router.post("/tell/action")
        def tell_action(action):
            self.publish_actions(action)


"""
141.19.44.


  "class_scanerControll": {
    "I1": {
      "_id": "class_scanerControll-I1",
      "_url": "",
      "_subscribers": {},
      "_subscriptions": {"class_MQTT-I1": "get_action"}
    }
  }



'/start_scan', methods=['POST']
'/stop_scan', methods=['POST']
'/reset_scan', methods=['POST']

'/lsc/get_status', methods=['GET']
'/lsc/get_position', methods=['GET']
'/lsc/set_do_ref', methods=['POST']

'/ham/get_ham_status', methods=['GET']

class_serverMeasurements
"""