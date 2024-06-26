from queue import Queue
import json
import requests
from fastapi import APIRouter
# from .class_ComponentABC import Component
# from .class_Event import Event

# class class_Aggregation (Component):
class class_Aggregation ():
    # def __init__(self, _conf):
    def __init__(self):

        self._router = APIRouter()
        self.configure_router()

        # for item in _conf:
        #     self.__setattr__(item, _conf[item])


        self.dts = ["425fc7d9e7fa4c63b01502b8c5dce7bb", "c6f3e4ef852546108fb3d773b88929e6", "cbadc4d3856542b6a14772ee00e3025a"]
        self.dt_methods = {}
        self.sequence = {}

        self.Q = Queue()

    def run(self):
        for dt in self.dts:
            self.dt_methods[dt] = self.get_all(dt, "_methods")
            # check connectivity
            url = f"http://141.19.44.18:8181/dt-{dt}/docs"
            try:
                response = requests.get(url)
                if response.ok:  # alternatively you can use response.status_code == 200
                    print("Success - API is accessible.")
                else:
                    print(f"Failure - API is accessible but sth is not right. Response code : {response.status_code}")
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                print(f"Failure - Unable to establish connection: {e}.")
            except Exception as e:
                print(f"Failure - Unknown error occurred: {e}.")

    def get_all(self, dt, attribute):
        url = f"http://141.19.44.18:8181/dt-{dt}/get{attribute}"
        try:
            response = requests.get(url)
            if response.ok:  # alternatively you can use response.status_code == 200
                response = response.json()
                print(response)
                return response[dt][attribute]
            else:
                print(f"Failure - API is accessible but sth is not right. Response code : {response.status_code}")
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            print(f"Failure - Unable to establish connection: {e}.")
        except Exception as e:
            print(f"Failure - Unknown error occurred: {e}.")

    def run_seq(self):
        if self.sequence != {}:
            for step in self.sequence:
                dt = self.sequence[step]["dt"]
                child = self.sequence[step]["child"]
                method = self.sequence[step]["method"]
                if "parameters" in self.sequence[step]:
                    parameters = ", ".join(param for param in self.sequence[step]["parameters"])
                    url = f"http://141.19.44.18:8181/dt-{dt}/childdo/{child}/{method}?params={parameters}"
                else:
                    url = f"http://141.19.44.18:8181/dt-{dt}/childdo/{child}/{method}"

                response = requests.get(url)
                print(response)


    def configure_router(self):
        @self._router.post("/set_sequence")
        def set_sequence(sequence):
            {0: {"dt": "12343567662524", "child": "gddll", "method": "blblbblb", "parameters": []}}
            return "sequence set!"

        @self._router.post("/run_sequence")
        def run_sequence():
            if self.sequence != {}:
                for step in self.sequence:
                    dt = self.sequenc[step]["dt"]
                    child = self.sequenc[step]["child"]
                    method = self.sequenc[step]["method"]
                    if "parameters" in self.sequenc[step]:
                        parameters = ", ".join(param for param in self.sequenc[step]["parameters"])
                        url = f"http://141.19.44.18:8181/dt-{dt}/childdo/{child}/{method}?params={parameters}"
                    else:
                        url = f"http://141.19.44.18:8181/dt-{dt}/childdo/{child}/{method}"

                    requests.get(url)

            return "sequence started!"



tt = class_Aggregation()
tt.run()

print(json.dumps(tt.dt_methods, indent=2))

tt.sequence = {
    0: {
        "dt": "cbadc4d3856542b6a14772ee00e3025a",
        "child": "class_MQTT-I1",
        "method": "publish",
        "parameters": ["test/hello/schnitzel", '{"schnitzel": "jaegerart"}']
    },
    1: {
        "dt": "cbadc4d3856542b6a14772ee00e3025a",
        "child": "class_MQTT-I1",
        "method": "publish",
        "parameters": ["test/hello/pommes", '{"pommes": "jaegerart"}']
    },
    2: {
        "dt": "cbadc4d3856542b6a14772ee00e3025a",
        "child": "class_MQTT-I1",
        "method": "publish",
        "parameters": ["test/hello/salat", '{"salat": "jaegerart"}']
    }
}

tt.run_seq()