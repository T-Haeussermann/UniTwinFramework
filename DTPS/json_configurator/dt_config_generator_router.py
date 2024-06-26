import json
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from fastapi import Request, HTTPException
import os

router = APIRouter()
templates = Jinja2Templates(directory="json_configurator/templates")

def loadClassTemplates(jsonPath):
    templates = {}

    for file_name in os.listdir(jsonPath):
        if file_name.endswith(".json") and file_name != "class_instance_data.json":
            with open(os.path.join(jsonPath, file_name)) as file:
                templates[file_name.replace(".json", "")] = json.load(file)
        else:
            pass
    return templates

# Load templates from the JSON files
jsonPath = "json_configurator/templates/jsonFiles/"
class_templates = loadClassTemplates(jsonPath)

with open(jsonPath + "class_instance_data.json") as file:
    class_instance_data = json.load(file)

# get class names from directory
class_names = list(class_templates.keys())


def get_latest_instance_name(class_name, class_instance_data):
    instances = class_instance_data.get(class_name, {})
    instance_names = list(instances.keys())
    if instance_names:
        instance_names.sort()
        return instance_names[-1]
    return None

@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "class_names": class_names,
        "class_templates": class_templates,
        "class_instance_data": json.dumps(class_instance_data)
    })

@router.post("/add_class/")
def add_class(class_name: str):
    class_instance_data[class_name] = {}
    return {"success": True}

@router.get("/get_data/")
def get_data():
    return class_instance_data

@router.post("/add_instance/")
async def add_instance(request_data: Request):
    request_data = await request_data.form()
    class_name = request_data.get("class_name")
    instance_name = request_data.get("instance_name")


    # Check if the requested class_name has a corresponding template, and if not, set an empty template
    instance_model = class_templates.get(class_name, {}).copy()

    # Set the id of the instance
    instance_model["_id"] = instance_model["_id"] + "-" + instance_name

    class_instance_data.setdefault(class_name, {})[instance_name] = instance_model
    return {"success": True}

@router.post("/delete_instance/")
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

@router.post("/clear_data/")
async def clear_data():
    class_instance_data.clear()  # Clear the JSON data
    return {"success": True}