from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Annotated
import json
import uvicorn
import os


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define instance templates
class_instance_data = {
}

class_influx_template = {
    "_id": "class_Influxdb",
    "_url": "ts-db-svc.dt:8086",
    "_token": "e-mrfQpl5pAhw-YI_XjYBGMD7ZbdFEupbPN-2hogFPK5KAaXBvlY1gnEhhG7kw1NIjrA03Ov9hMTOSI57Dr-fg==",
    "_org": "unitwin",
    "_subscribers": {
        "class_TSDanalyse": "predict"
    }
}

class_mqtt_template = {
    "_id": "class_MQTT",
    "_username": "dbt",
    "_passwd": "dbt",
    "_host": "mq.jreichwald.de",
    "_port": 1883,
    "_topic_sub": ["Topic1", "Topic2", "Measurement"],
    "_subscribers": {
        "method_MQTT": "method_MQTT"
    }
}

method_mqtt_template = {
    "_id": "method_MQTT",
    "_subscriptions": {
    "class_MQTT": "method_MQTT"
    }
}

class_dataverse_template = {
    "_id": "Dataverse",
    "_BASE_URL": "http://141.19.44.70:8080",
    "_dir": "C:\\Users\\therm\\Documents\\Arbeit\\HSMannheim\\10-Projekte\\UniTwin\\folderToWatch",
    "_rootDataverse": "hsma"
}

class_TSDanalyse_template = {
    "_id": "class_TSDanalyse",
    "threading": "run"
}

class_names = ['class_Dataverse', 'class_Influxdb', 'class_Leaf', 'class_MQTT', 'class_TSDanalyse', 'method_Dataverse', 'method_Leaf', 'method_MQTT']

def get_latest_instance_name(class_name, class_instance_data):
    instances = class_instance_data.get(class_name, {})
    instance_names = list(instances.keys())
    if instance_names:
        instance_names.sort()
        return instance_names[-1]
    return None

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "class_names": class_names,
        "class_influx_template": class_influx_template,
        "class_mqtt_template": class_mqtt_template,
        "method_mqtt_template": method_mqtt_template,
        "class_dataverse_template": class_dataverse_template,
        "class_TSDanalyse_template": class_TSDanalyse_template,
        "class_instance_data": json.dumps(class_instance_data)
    })
@app.post("/add_class/")
def add_class(class_name: str):
    class_instance_data[class_name] = {}
    return {"success": True}

@app.get("/get_data/")
def get_data():
    return class_instance_data

@app.post("/add_instance/")
async def add_instance(request_data: Request):
    request_data = await request_data.form()
    class_name = request_data.get("class_name")
    instance_name = request_data.get("instance_name")

    if class_name == 'class_MQTT':
        instance_model = class_mqtt_template.copy()
    elif class_name == 'method_MQTT':
        instance_model = method_mqtt_template.copy()
    elif class_name == 'class_Influxdb':
        instance_model = class_influx_template.copy()
    elif class_name == 'class_Dataverse':
        instance_model = class_dataverse_template.copy()
    elif class_name == 'class_TSDanalyse':
        instance_model = class_TSDanalyse_template.copy()
    else:
        instance_model = {}

    class_instance_data.setdefault(class_name, {})[instance_name] = instance_model
    return {"success": True}
@app.post("/delete_instance/")
async def delete_instance(request_data: Request):
    request_data = await request_data.form()
    class_name = request_data.get("class_name")
    instance_name = request_data.get("instance_name")
    if class_name in class_instance_data and instance_name in class_instance_data[class_name]:
        del class_instance_data[class_name][instance_name]
        # Check if the class has no more instances and remove the class entry if necessary
        if not class_instance_data[class_name]:
            del class_instance_data[class_name]
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Instance not found")

"""rund API server. swagger ui on http://127.0.0.1:8000/docs#/"""
# uvicorn.run(app, host="0.0.0.0", port=1234, log_level="info")