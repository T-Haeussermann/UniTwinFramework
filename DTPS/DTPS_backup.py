import json
import os.path
import io
import zipfile
import pickle
import requests
from threading import Thread
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
from digitwin import DigitalTwin, DigitalTwinSchema
from serializer import MongoDTSerializer
from confstorage import MongoConfSerializer
from Functions.deployTwin import deployTwin, createDeployment, createService, createIngress
from Functions.deleteTwin import deleteTwin
from Functions.existTwin import existTwin
from Functions.defineTwin import defineTwin
from Functions.mountTwin import mountTwin
from Functions.listTwins import listTwins
from json_configurator import dt_config_generator_router

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
        status = existTwin(defineTwin(uid, version))
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

# check for twins active in last run based on memory
if os.path.isfile("./memory/listDT.pkl") == True:
    with open('./memory/listDT.pkl', 'rb') as input:
        memorylistDT = pickle.load(input)
print("memorylistDT: " + str(memorylistDT))

# check active twins in cluster
for item in listTwins(namespace):
    clusterlistDT.append(item.replace("dt-", ""))
print("clusterlistDT: " + str(clusterlistDT))

# merge two lists without duplicates
listDT = list(set(memorylistDT + clusterlistDT))

# reinstantiate dt
for item in listDT:
    reinstantiate(item)


"""create API"""
app = FastAPI()
app.mount("/static", StaticFiles(directory="json_configurator/static"), name="static")
app.include_router(dt_config_generator_router.router)

"""define API Methods"""
@app.get("/createTwin")
async def createTwin(conf, version="1.0"):
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
    deployTwin(defineTwin(uid, version))

    # add DT to listDT and write to pkl
    listDT.append(uid)
    print(listDT)
    with open('./memory/listDT.pkl', 'wb') as output:
        output.truncate()
        pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)

    return {uid: "started successfully", "version": version}

@app.get("/loadTwin/{uid}")
async def loadTwin(uid, version="1.0"):
    # uid = "63fef629bc9a31ef779e85db"

    # load dt with uid
    dt = loaddt(uid)

    if dt != None:
        uid = str(dt._id)
        status = existTwin(defineTwin(uid, version))
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
    return status

@app.get("/updateConf/{uid}")
async def updateConf(conf, uid):
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

        try:
            # trigger DT to update its configuration and add new classes
            url = "http://dt-" + uid + "-svc.dt.svc.cluster.local:7000/learn"
            Thread(target=requests.get, args=[url], daemon=True).start()
            return {uid: {"status": "configuration updated"}}
        except:
            return {uid: "twin not running"}
    except:
        return {uid: "invalid configuration. No changes!"}

@app.get("/enum")
async def enum():
    resp = {"Twins": {"Number": len(listDT), "Names": listDT}}
    return resp

@app.get("/delete/{uid}")
async def stopTwin(uid):
    try:
        status = str(deleteTwin(defineTwin(uid, version=None)))
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

@app.get("/deleteAll")
async def stopAllTwins():
    for dt in listDT:
        print(deleteTwin(defineTwin(dt, version=None)))
    listDT.clear()
    print(listDT)
    with open('./memory/listDT.pkl', 'wb') as output:
        output.truncate()
        pickle.dump(listDT, output, pickle.HIGHEST_PROTOCOL)
    return {"status": "All Digital Twins deleted"}

@app.get("/mount/{uid}/{path}")
async def mount(uid, path, version="1.0"):
    # mount directory for twin
    resp = mountTwin(defineTwin(uid, version), path)
    print(resp)

@app.get('/provide/{name}')
def download_file(name):
    filenames = []
    files = providePaths(name)
    for file in files:
        filenames.append(files[file]["path"])
    return zipfiles(filenames)

"""rund API server. swagger ui on http://127.0.0.1:8000/docs#/"""
uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
