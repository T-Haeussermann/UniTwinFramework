import random
from queue import Queue
import json
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

class class_Part(Component):
    def __init__(self, _conf):

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.methods = {}
        self.Q = Queue()

    def configure_router(self):
        # self._router.mount("/line", StaticFiles(directory="static", html=True), name="static")

        @self._router.get("/get-pos")
        def get_pos():
            return self.pos_data

        @self._router.post("/update-pos")
        def get_pos(pos_data):
            self.pos_data = pos_data
            return {"msg": "updated position data"}

        @self._router.get("/get-methods")
        async def get_methods():
            return self.parent._methods

        @self._router.get("/get-skills/")
        async def get_skills():
            return self.skills

        @self._router.post("/exec-skill")
        async def exec_skill():
            return self.parent._methods

        @self._router.get("/get-status")
        async def get_status(id):
            status = random.choice(["active", "inactive"])
            return {"status": status}

        @self._router.get("/get-value/")
        async def get_status(id):
            value = random.randint(0, 100)
            return {"value": value}

        # rs232
        # rs485
        # can