import json
import time
import threading
from Modules.class_Composite import Composite
import uvicorn
import os
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi import Request
import traceback
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import html
import requests
#from Chat.method_chat import chatbot_response

# for Operation Availability testing
start = None
def track_time():
    global start
    start = time.time()
    print(f"Start time: {start}")
    print(f"End time after 1 hour: {start + 3600}")
    time.sleep(3600)  # Sleep for 1 hour
    end = time.time()
    print(f"End time after 1 hour: {end}")

# Start the tracking thread
time_thread = threading.Thread(target=track_time, daemon=True)
time_thread.start()
# for Operation Availability testing

"""Variables"""
uid = None
uidFile = Path("uid.json")
standalone = bool(os.getenv("STANDALONE"))
if standalone == None:
    standalone = False

"""check for standalone mode"""
if standalone == False:
    """check if uid.json file exists. necessary for restart of docker container (keep uid). else get uid from env"""
    if uidFile.is_file() == True:
        # Opening JSON file
        f = open(uidFile)
        # returns JSON object as a dictionary
        uid = json.load(f)
        # Closing file
        f.close()
        uid = uid["uid"]

    else:
        # for docker
        uid = os.environ["uid"]

        uidDict = {"uid": uid}

        # Opening JSON file
        f = open(uidFile, "w")

        # dump JSON object as a dictionary
        json.dump(uidDict, f, indent=4)

        # Closing file
        f.close()

elif standalone == True:
    from Modules.class_Composite_standalone import Composite_Standalone
    uid = os.getenv("UID")
    if uid == None:
        uid = "00000000000000000000000000000000"

"""create DT object and start instantiation"""
print(type(standalone))
print(standalone)
if standalone is False:
    twin = Composite(uid)
elif standalone == True:
    conf = json.loads(os.getenv("CONFIGURATION"))
    twin = Composite_Standalone(uid, conf)

twin.process()

print(twin._uid)
#from Chat.method_chat import chatbot_response
# for Operation Availability testing
print(f"end init time: {time.time()}")
# for Operation Availability testing
# for scaling efficiency testing
params = {"uid": twin._uid}
response = requests.post("http://dtps-svc.dt.svc.cluster.local:8000/ready", json=params, timeout=5)
# for scaling efficiency testing

"""create API"""
if standalone == False:
    rootPath = "/dt-" + str(uid) # + "/api/v1"
    app = FastAPI(root_path=rootPath) #root_path=rootPath, openapi_url='/openapi.json')

    app.mount("/Chat/static/styles", StaticFiles(directory="Chat/static/styles"), name="static")

    """change digitalTwinUrl in index.html and load"""
    # digitalTwinUrl = '"http://localhost/dt-' + uid + '/chat/get"'
    digitalTwinUrl = '"http://141.19.44.18:8181/dt-' + uid + '/chat/get"'
    pathHTML = 'Chat/templates/index.html'

    with open(pathHTML, 'r') as f:
        html_text = f.read()
        f.close()

    html_text = html.unescape(html_text)
    html_text = html_text.replace("digitalTwinUrl", digitalTwinUrl)

    with open(pathHTML, 'w') as f:
        f.write(html_text)

    templates = Jinja2Templates(directory="Chat/templates")

elif standalone == True:
    app = FastAPI()


'''Define functions'''
def map_arguments_to_function(func, argument_strings):
    # Get the parameter names of the function
    parameter_names = list(func.__code__.co_varnames[:func.__code__.co_argcount])

    # Create a dictionary to hold the parameter values
    argument_dict = {}

    for arg_string in argument_strings:
        key, value = arg_string.split('=')
        key = key.strip()
        value = value.strip()
        argument_dict[key] = value

    # Create a dictionary with default values for all parameters
    default_values = {param: None for param in parameter_names}
    argument_dict = {param: argument_dict.get(param, default_values[param]) for param in default_values}

    # Remove entries with None values
    argument_dict = {key: value for key, value in argument_dict.items() if value is not None}

    # Call the function with the dynamically mapped arguments
    return argument_dict

"""define API Methods"""
"""add all routers defined in children to UniTwinGenerator app"""
for child in twin._children:
    if hasattr(child, "_router"):
        app.include_router(child._router)
        print("Added router for child " + child._id)

@app.get("/get")
async def getAtt(Att):
    try:
        result = str(getattr(twin, Att))
    except:
        result = []
        for child in twin._children:
            if hasattr(child, Att):
                result.append(str(getattr(child, Att)))
        if len(result) == 1:
                result = result[0]
        elif len(result) == 0:
            result = "not found"
    return {twin._uid: {Att: result}}


if standalone == False:
    @app.get("/learn")
    async def learn():
        diff = twin.learn()
        for item in diff["learnd"]:
            for instance in diff["learnd"][item]:
                child = twin.getChild(instance)
                if hasattr(child, "_router"):
                    app.include_router(child._router)
                    app.openapi_schema = None
                    app.setup()
                    print("Added router for child " + child._id)

        for router in diff["routers"]:
            for item in router.__dict__["routes"]:
                for route in app.routes:
                    if route.name == item.name:
                        app.routes.remove(route)
                        app.openapi_schema = None
                        app.setup()
                        print("Removed route " + str(route))

        # for reconfiguration time testing
        params = {"uid": twin._uid}
        requests.post("http://dtps-svc.dt.svc.cluster.local:8000/ready", json=params, timeout=5)
        # for reconfiguration time testing

    @app.get("/chat", response_class=HTMLResponse)
    # def mainpage(request: Request):
    #     return templates.TemplateResponse("index.html", {"request": request})
    async def read_item(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/chat/get")
    def get_bot_response(msg: str, model: str):
        print(model)

        if model == "bm":
            # url = f"http://chatmodelprovider-svc.dt.svc.cluster.local:5000/chat/get?msg={msg}"
            url = "http://chatmodelprovider-svc.dt.svc.cluster.local:5000/chat/get"
            params = {"msg": msg}
            try:
                resp = requests.get(url, params=params).json()
                print(resp)
            except requests.exceptions.ConnectionError as er:
                return f"Basic model not reachable."

            for item in resp:
                if item != "generic_action":
                    placeholders = re.findall(r'{(.*?)}', resp[item])
                    if placeholders != []:
                        for placeholder in placeholders:
                            value = getattr(twin, placeholder)
                            if isinstance(value, list):
                                formatted_value = ""
                                for obj in value:
                                    try:
                                        formatted_value = formatted_value + "<br />" + str(obj._id) + ",<br />"
                                    except:
                                        formatted_value = formatted_value + "<br />" + str(obj) + ",<br />"
                            elif isinstance(value, dict):
                                formatted_value = ""
                                for obj in value:
                                    formatted_value = formatted_value + "<br />" + str(obj) + ",<br />"
                            else:
                                formatted_value = str(value)
                            resp = resp[item].replace(f"{{{placeholder}}}", formatted_value)
                    else:
                        resp = resp[item]
                elif item == "generic_action":
                    child = resp[item]["child"]
                    child = twin.getChild(child)
                    parameters = resp[item]["parameters"]
                    if child != None:
                        methodname = resp[item]["method"]
                        try:
                            method = getattr(child, methodname)
                            try:
                                parameters = map_arguments_to_function(method, parameters)
                                method(**parameters)
                                resp = f"Running method {methodname} with parameters {parameters} of child {child._id}"
                            except Exception as e:
                                traceback.print_exc()
                                resp = f"Parameters {parameters} not valid for method {methodname} in child {child._id}"
                        except Exception as e:
                            traceback.print_exc()
                            resp = f"Method {methodname} not found in child {child._id}!"
                    else:
                        resp = "Child not found"
            print(resp)
            return resp

        elif model == "llm":
            tools = twin._tools
            # url = "http://chatmodelprovider-svc.dt.svc.cluster.local:5000/fctcalling"
            url = "http://141.19.44.64:5050/fctcalling"
            # url = "http://141.19.44.216:5050/fctcalling"
            tools = json.dumps(tools)
            params = {"prompt": msg, "tools": tools}
            print(params)
            print(type(params))
            print(tools)
            print(type(tools))
            headers = {
                'accept': 'application/json',
            }
            try:
                response = requests.get(url, params=params, headers=headers)
                response = response.json()
                print(response)
            except requests.exceptions.ConnectionError as er:
                return f"LLM model not reachable."

            if "call" in response:
                raw_function_name_and_params = response['call']['function_name']
                split_data = raw_function_name_and_params.split("\n", 1)
                function_name = split_data[0].split(".")[-1]
                function_params = json.loads(split_data[1] if len(split_data) > 1 else "{}")
                print(function_name)
                print(function_params)

                # for child methods
                if function_name != "describe":
                    for child in twin._children:
                        if hasattr(child, function_name):
                            print("Found it!")
                            method = getattr(child, function_name)
                            method(**function_params)
                            resp = f"Running method {function_name} with parameters {function_params} of child {child._id}"
                            print(resp)
                            return resp

                # for attribute description
                elif function_name == "describe":
                    value = twin.describe(**function_params)
                    resp = f"Attribute {function_params['attribute']} is: {value}"
                    print(resp)
                    return resp

            elif "message" in response:
                resp = response["message"]
                print(resp)
                return resp
            else:
                pass

@app.post("/childdo/")
def childDo(child, do, params: dict = None):
    child = twin.getChild(child)
    method = getattr(child, do)
    if params == None:
        resp = method()
    else:
        #params = params.replace(" ", "")
        #params = params.split(",")
        print(params)
        resp = method(**params)
    return resp

@app.get("/childQ")
def childQput(child, msg, Q="Q"):
    try:
        child = twin.getChild(child)
        getattr(child, Q).put(msg)
        return "Appended msg to child queue"
    except:
        return "No such child or child without a queue"

"""rund API server. swagger ui on http://127.0.0.1:7000/docs#/"""
if standalone == False:
    uvicorn.run(app, host="0.0.0.0", port=7000, log_level="info", root_path=rootPath)
else:
    uvicorn.run(app, host="0.0.0.0", port=7000, log_level="info")


