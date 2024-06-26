import json
import os.path
import io
import zipfile
import pickle
import requests
from fastapi import FastAPI, BackgroundTasks, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
from digitwin import DigitalTwin, DigitalTwinSchema
from serializer import MongoDTSerializer
from confstorage import MongoConfSerializer
from Functions.class_kube_twin import kube_twin
from json_configurator import dt_config_generator_router
import traceback

"""Variables"""
listDT = []
memorylistDT = []
clusterlistDT = []
namespace = "dt"

# Warm up databases so there's already a connection made
MongoDTSerializer.initialize()
MongoConfSerializer.initialize()

def providePaths(name):
    # get module path
    module = name + ".py"
    modulepath = "Modules/" + module
    files = {"class": {"path": modulepath, "name": module}}

    # get description path
    try:
        description = name + ".json"
        descriptionpath = "Descriptions/" + description
        files["description"] = {"path": descriptionpath, "name": module}

    except:
        print("No description found for this module.")

    return files

def zipfiles(filenames):
    zip_filename = "%s.zip"

    # Open StringIO to grab in-memory ZIP contents
    s = io.BytesIO() #io.StringIO()
    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = fname

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(),
                    media_type="application/x-zip-compressed",
                    headers={"Content-Disposition": f"attachment; filename={zip_filename}"})
    return resp

def createdt():
    d1 = DigitalTwin()
    dtschema = DigitalTwinSchema()
    if d1._id not in listDT:
        print(dtschema.dump(d1))
        MongoDTSerializer.persist(dtschema.dump(d1))
        print("Created and serialized digital twin with id %s" % d1)
        return d1
    else:
        print("Resume based on duplicate uid")
        createdt()

def loaddt(uid):
    twin = None
    dtschema = DigitalTwinSchema()
    fetched_data = MongoDTSerializer.load_twin(uid)
    print(fetched_data)
    if fetched_data != None and len(fetched_data) > 0:
        twin = dtschema.load(fetched_data)
        print("loaded.")
        return twin
    return None

def reinstantiate(uid, version="1.0"):
    # load dt with uid
    dt = loaddt(uid)

    if dt != None:
        uid = str(dt._id)
        status = kube_twin_manager.loadTwin(kube_twin_manager.defineTwin(uid, version))
        print(status)
        if status["deployment"] != "already running":
            # add DT to listDT and write to pkl
            listDT.append(uid)
            print(listDT)
            with open('./memory/listDT.pkl', 'wb') as output:
                output.truncate()
                pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)
    else:
        status = {"status": f"{uid} for loading not found, try create"}
        print(status)

def twinLearn(uid, url):
    try:
        resp = requests.get(url)
        print(f"{uid}: triggern /learn. Result {resp}. Success!")
    except:
        print(f"{uid}: triggern /learn. Failed! Twin is not running.")


# create instance of kube_twin to manage twins
kube_twin_manager = kube_twin(namespace)

# check for twins active in last run based on memory
if os.path.isfile("./memory/listDT.pkl") == True:
    with open('./memory/listDT.pkl', 'rb') as input:
        memorylistDT = pickle.load(input)
print("memorylistDT: " + str(memorylistDT))

# check active twins in cluster
for item in kube_twin_manager.listTwins(namespace):
    if "dt-" in item and item != "cs" and item != "dt-db" and item != "dtps" and item != "grafana" and item != "os" and item != "ts-db":
        clusterlistDT.append(item.replace("dt-", ""))
print("clusterlistDT: " + str(clusterlistDT))

# merge two lists without duplicates
listDT = list(set(memorylistDT + clusterlistDT))

# reinstantiate dt
for item in listDT:
    reinstantiate(item)

"""create API"""
rootPath = "/dtps"
App = FastAPI(root_path=rootPath)
App.mount("/json_configurator/static", StaticFiles(directory="json_configurator/static"), name="static")
App.include_router(dt_config_generator_router.router)

"""define API Methods"""
@App.post("/createTwin")
async def createTwin(conf, version="1.0", assignNode=False, node_name=None):
    # error handling for wrong conf
    try:
        conf = json.loads(conf)
    except:
        return "Invalid configuration"

    # create dt to get uid
    dt = createdt()
    uid = str(dt._id)
    id = {'_id': uid}

    # Serialize DT

    MongoConfSerializer.persist( id | conf)

    # start unitwin deployment on kubernetes
    kube_twin_manager.deployTwin(kube_twin_manager.defineTwin(uid, version), assignNode, node_name)

    # add DT to listDT and write to pkl
    listDT.append(uid)
    print(listDT)
    with open('./memory/listDT.pkl', 'wb') as output:
        output.truncate()
        pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)

    return {uid: "started successfully", "version": version}

@App.post("/loadTwin/{uid}")
async def loadTwin(uid, version="1.0", assignNode=False, node_name=None):
    # uid = "63fef629bc9a31ef779e85db"

    # load dt with uid
    dt = loaddt(uid)

    if dt != None:
        uid = str(dt._id)
        status = kube_twin_manager.loadTwin(kube_twin_manager.defineTwin(uid, version), assignNode, node_name)
        print(status)
        if status["deployment"] != "already running":
            # add DT to listDT and write to pkl
            listDT.append(uid)
            print(listDT)
            with open('./memory/listDT.pkl', 'wb') as output:
                output.truncate()
                pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)
    else:
        status = {"status": f"{uid} for loading not found, try create"}
        print(status)
    return str(status)

@App.get("/getConf/{uid}")
async def getConf(uid):
    # get conf
    conf = MongoConfSerializer.load_twin(uid)

    return {"conf": conf}

@App.post("/updateConf/{uid}")
async def updateConf(conf, uid, background_tasks: BackgroundTasks):
    # get old conf to use if any problems occure
    oldConf = MongoConfSerializer.load_twin(uid)

    # define id
    idDT = {'_id': uid}

    # delete old conf
    MongoConfSerializer.delete_conf(uid)

    try:
        # dump new conf
        conf = json.loads(conf)
        MongoConfSerializer.persist(idDT | conf)

        # trigger DT to update its configuration and add new instances
        url = "http://dt-" + uid + "-svc.dt.svc.cluster.local:7000/learn"
        background_tasks.add_task(twinLearn, uid, url)
        return {uid: "updated configuration."}
    except Exception as e:
        traceback.print_exc()
        return {uid: "invalid configuration. No changes!"}

@App.post("/addConfInstance/{uid}")
async def removeConf(class_name, instance_conf, uid, background_tasks: BackgroundTasks):
    # get old conf to use if any problems occure
    conf = MongoConfSerializer.load_twin(uid)

    # define id
    idDT = {'_id': uid}

    try:
        # Update conf
        if class_name in conf:
            conf[class_name]["I" + str(len(conf[class_name])+1)] = json.loads(instance_conf)
        else:
            conf[class_name] = {}
            conf[class_name]["I1"] = json.loads(instance_conf)

        # delete old conf
        MongoConfSerializer.delete_conf(uid)

        # dump new conf
        MongoConfSerializer.persist(idDT | conf)

        # trigger DT to update its configuration and add new instances
        url = "http://dt-" + uid + "-svc.dt.svc.cluster.local:7000/learn"
        background_tasks.add_task(twinLearn, uid, url)
        return {uid: "updated configuration."}
    except Exception as e:
        traceback.print_exc()
        return {uid: "invalid configuration. No changes!"}



@App.delete("/removeConfInstance/{uid}")
async def removeConf(class_name, instance, uid, background_tasks: BackgroundTasks):
    # get old conf to use if any problems occure
    conf = MongoConfSerializer.load_twin(uid)

    # define id
    idDT = {'_id': uid}

    try:
        # Update conf
        if class_name in conf and instance in conf[class_name]:
            if len(conf[class_name]) == 1:
                del conf[class_name]
            else:
                conf[class_name].pop(instance)
        else:
            return "Not found"

        # delete old conf
        MongoConfSerializer.delete_conf(uid)

        # dump new conf
        MongoConfSerializer.persist(idDT | conf)

        # trigger DT to update its configuration and add new instances
        url = "http://dt-" + uid + "-svc.dt.svc.cluster.local:7000/learn"
        background_tasks.add_task(twinLearn, uid, url)
        return {uid: "updated configuration."}
    except Exception as e:
        traceback.print_exc()
        return {uid: "invalid configuration. No changes!"}

@App.get("/enum")
async def enum():
    resp = {"Twins": {"Number": len(listDT), "Names": listDT}}
    return resp

@App.delete("/delete/{uid}")
async def stopTwin(uid):
    try:
        status = str(kube_twin_manager.deleteTwin(kube_twin_manager.defineTwin(uid, version=None)))
        print(status)
        # remove DT from listDT and write to pkl
        listDT.remove(uid)
        print(listDT)
        with open('./memory/listDT.pkl', 'wb') as output:
            output.truncate()
            pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)
    except:
        status = {"status": f"{uid} for deletion not found"}
        print(status)
    return status

@App.delete("/deleteAll")
async def stopAllTwins():
    for dt in listDT:
        print(kube_twin_manager.deleteTwin(kube_twin_manager.defineTwin(dt, version=None)))
    listDT.clear()
    print(listDT)
    with open('./memory/listDT.pkl', 'wb') as output:
        output.truncate()
        pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)
    return {"status": "All Digital Twins deleted"}

@App.get("/mount/{uid}/")
async def mount(uid, path: str, version="1.0"):
    # mount directory for twin
    resp = kube_twin_manager.mountTwin(kube_twin_manager.defineTwin(uid, version), path)
    return resp

@App.get('/provide/{name}')
def download_file(name):
    filenames = []
    files = providePaths(name)
    for file in files:
        filenames.append(files[file]["path"])
    return zipfiles(filenames)

@App.get('/list/nodes')
def listNodes():
    return kube_twin_manager.listNodes()

@App.get('/list/currentNode/{uid}')
def listCurrentNodes(uid):
    deployment_name = "dt-" + uid
    return kube_twin_manager.listCurrentNode(deployment_name, namespace)

@App.post('/assign/{uid}/{node_name}')
def assignNode(uid, node_name):
    # assign dt to node
    deployment_name = "dt-" + uid
    return kube_twin_manager.assignNode(deployment_name, namespace, node_name)

"""rund API server. swagger ui on http://127.0.0.1:8000/docs#/"""
uvicorn.run(App, host="0.0.0.0", port=8000, log_level="info")
