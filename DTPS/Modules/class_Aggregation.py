from queue import Queue
import json
import random
import html
import requests
from typing import List, Dict
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from starlette.responses import FileResponse
from .class_ComponentABC import Component
from .class_Event import Event


class class_Aggregation(Component):
    def __init__(self, _conf):
        self.dt_methods = {}
        self.dt_skills = {}
        self.pos_data = {}
        self.sequence = {}

        self.html_file = "Modules/templates/class_Aggregation_index.html"

        self.Q = Queue()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self._router = APIRouter()
        self.configure_router()

    def run(self):
        with open(self.html_file, 'r') as f:
            html_text = f.read()
            html_text = html.unescape(html_text)
            html_text = html_text.replace("dt-uid", f"dt-{self.parent._uid}")
            print(html_text)

        with open(self.html_file, 'w') as f:
            f.write(html_text)

        # check connectivity
        for dt in self.dts:
            # url = f"http://141.19.44.18:8181/dt-{dt}/docs#/default"
            url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/docs#/default"
            try:
                response = requests.get(url)
                print("response.status_code")
                print(response.status_code)
                if response.ok:  # alternatively you can use response.status_code == 200
                    print("Success - API is accessible.")
                else:
                    print(f"Failure - API is accessible but sth is not right. Response code : {response.status_code}")
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                print(f"Failure - Unable to establish connection: {e}.")
            except Exception as e:
                print(f"Failure - Unknown error occurred: {e}.")

        self.get_data()

    def get_data(self):
        # get positions ,methods and skills
        for dt in self.dts:
            # url = f"http://141.19.44.18:8181/dt-{dt}/get-pos/"
            url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/get-pos"
            print(url)
            try:
                response = requests.get(url)
                dt_pos_data = response.json()
                self.pos_data[dt] = dt_pos_data
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                print(f"Failure - Unable to establish connection: {e}.")
            except Exception as e:
                print(f"Failure - Unknown error occurred: {e}.")

            # url = f"http://141.19.44.18:8181/dt-{dt}/get-methods/"
            url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/get-methods/"
            try:
                response = requests.get(url)
                dt_methods = response.json()
                self.dt_methods[dt] = dt_methods
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                print(f"Failure - Unable to establish connection: {e}.")
            except Exception as e:
                print(f"Failure - Unknown error occurred: {e}.")

            # url = f"http://141.19.44.18:8181/dt-{dt}/get-skills"
            url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/get-skills"
            try:
                response = requests.get(url)
                dt_skills = response.json()
                self.dt_skills[dt] = dt_skills
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                print(f"Failure - Unable to establish connection: {e}.")
            except Exception as e:
                print(f"Failure - Unknown error occurred: {e}.")

        self.pos_data = self.scale(self.remove_levels(self.pos_data))

    def run_seq(self):
        if self.sequence != {}:
            for step in self.sequence:
                # for dts part of this aggregation
                if "dt" in self.sequence[step]:
                    dt = self.sequence[step]["dt"]
                    child = self.sequence[step]["child"]
                    method = self.sequence[step]["method"]
                    if "parameters" in self.sequence[step]:
                        parameters = self.sequence[step]["parameters"]
                        # url = f"http://141.19.44.18:8181/dt-{dt}/childdo?child={child}&do={method}"
                        url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/childdo?child={child}&do={method}"
                    else:
                        # url = f"http://141.19.44.18:8181/dt-{dt}/childdo/{child}/{method}"
                        url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/childdo/{child}/{method}"
                        parameters = {}

                    response = requests.post(url, json=parameters)
                    print(response)

                # for aggregation dts as part of this aggregation
                else:
                    for dt in self.sequence[step]:
                        # url = f"http://141.19.44.18:8181/dt-{dt}/run_sequence"
                        url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/run_sequence"
                        response = requests.post(url)
                        print(response)

        else:
            print("No sequence defined")

    def scale(self, data):
        def find_max_dimensions(data, max_x=0, max_y=0):
            if isinstance(data, list):
                for rect in data:
                    max_x = max(max_x, rect["position"]["x"] + rect["width"])
                    max_y = max(max_y, rect["position"]["y"] + rect["height"])
            elif isinstance(data, dict):
                for key, value in data.items():
                    max_x, max_y = find_max_dimensions(value, max_x, max_y)
            return max_x, max_y

        def scale_rectangles(data, scale_x, scale_y):
            if isinstance(data, list):
                for rect in data:
                    rect["position"]["x"] = int(rect["position"]["x"] * scale_x)
                    rect["position"]["y"] = int(rect["position"]["y"] * scale_y)
                    rect["width"] = int(rect["width"] * scale_x)
                    rect["height"] = int(rect["height"] * scale_y)
            elif isinstance(data, dict):
                for key, value in data.items():
                    scale_rectangles(value, scale_x, scale_y)

        # Find the maximum dimensions for scaling
        max_x, max_y = find_max_dimensions(data)

        # Calculate scaling factors
        scale_x = 1000 / max_x if max_x != 0 else 1
        scale_y = 1000 / max_y if max_y != 0 else 1

        # Scale the coordinates and dimensions
        scale_rectangles(data, scale_x, scale_y)

        return data

    def remove_levels(self, data):
        exchange = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively flatten the nested dictionary
                flattened_dict = self.remove_levels(value)
                for sub_key, sub_value in flattened_dict.items():
                    exchange[sub_key] = sub_value
            else:
                exchange[key] = value
        return exchange

    def configure_router(self):
        # self._router.mount("/line", StaticFiles(directory="static", html=True), name="static")

        @self._router.get("/line")
        def line():
            return FileResponse(self.html_file)

        @self._router.get("/get-pos")
        async def get_rectangles():
            print(self.pos_data)
            return self.remove_levels(self.pos_data)

        @self._router.post("/upload-rectangles")
        def upload_rectangles(data: PositionData):
            self.pos_data = data.dict()["__root__"]
            scaled_data = self.scale(self.pos_data)
            self.pos_data = scaled_data
            return {"message": "Rectangles data received"}

        @self._router.post("/set-sequence")
        def set_sequence(sequence):
            self.sequence = {
                0: {
                    "dt": "12343567662524",
                    "child": "gddll",
                    "method": "blblbblb",
                    "parameters": {

                    }
                },
                1: {
                    "12343567662524": {
                        0: {
                            "dt": "12343567662524",
                            "child": "gddll",
                            "method": "blblbblb",
                            "parameters": {

                            }
                        },
                        1: {
                            "dt": "12343567662524",
                            "child": "gddll",
                            "method": "blblbblb",
                            "parameters": {

                            }
                        }
                    }
                },
                2: {
                    "dt": "12343567662524",
                    "child": "gddll",
                    "method": "blblbblb",
                    "parameters": {

                    }
                }
            }
            # self.sequence = sequence

            for step in self.sequence:

                # for dts part of this aggregation
                if "dt" in self.sequence[step]:
                    print(step)
                    print("do something if required with the DTs directly part of this aggregation twin")

                # for aggregation dts as part of this aggregation
                else:
                    for dt in self.sequence[step]:
                        print(step)
                        # url = f"http://141.19.44.18:8181/dt-{dt}/set_sequence?sequence={self.sequence[step][dt]}"
                        url = f"http://dt-{dt}-svc.dt.svc.cluster.local:7000/set_sequence?sequence={self.sequence[step][dt]}"
                        print(url)
                        # response = requests.post(url)
            return "sequence set!"

        @self._router.post("/run-sequence")
        def run_sequence():
            self.run_seq()
            return "sequence started!"


class Position(BaseModel):
    x: int
    y: int


class Rectangle(BaseModel):
    id: str
    position: Position
    width: int
    height: int
    value: bool
    status: bool


class PositionData(BaseModel):
    __root__: Dict[str, List[Rectangle]]

# self.pos_data = {
#                                         "c6f3e4ef852546108fb3d773b88929e1": [{"id": "C1", "position": {"x": 50, "y": 110}, "width": 80, "height": 200, "value": True, "status": False}],
#                                         "c6f3e4ef852546108fb3d773b88929e2": [{"id": "C2", "position": {"x": 200, "y": 50}, "width": 200, "height": 80, "value": False, "status": True}],
#                                         "c6f3e4ef852546108fb3d773b88929e3": [{"id": "C3", "position": {"x": 410, "y": 50}, "width": 200, "height": 80, "value": True, "status": False}],
#                                         "c6f3e4ef852546108fb3d773b88929e4": [{"id": "C4", "position": {"x": 560, "y": 110}, "width": 80, "height": 200, "value": False, "status": True}],
#                                         "c6f3e4ef852546108fb3d773b88929e5": [{"id": "M1", "position": {"x": 200, "y": 120}, "width": 50, "height": 50, "value": True, "status": False}],
#                                         "c6f3e4ef852546108fb3d773b88929e6": [{"id": "M2", "position": {"x": 410, "y": 120}, "width": 50, "height": 50, "value": False, "status": False}],
#                                         "00000000000000000000000000000000": {
#                                             "11111111111111111111111111111111": [{"id": "C1", "position": {"x": 550, "y": 610}, "width": 80, "height": 200, "value": True, "status": False}],
#                                             "22222222222222222222222222222222": [{"id": "C2", "position": {"x": 700, "y": 550}, "width": 200, "height": 80, "value": False, "status": True}],
#                                             "33333333333333333333333333333333": [{"id": "C3", "position": {"x": 910, "y": 550}, "width": 200, "height": 80, "value": True, "status": False}],
#                                             "44444444444444444444444444444444": [{"id": "C4", "position": {"x": 1060, "y": 610}, "width": 80, "height": 200, "value": False, "status": True}],
#                                             "55555555555555555555555555555555": [{"id": "M1", "position": {"x": 700, "y": 620}, "width": 50, "height": 50, "value": True, "status": False}],
#                                             "66666666666666666666666666666666": [{"id": "M2", "position": {"x": 910, "y": 620}, "width": 50, "height": 50, "value": False, "status": False}]
#                                         }
#                                     }
