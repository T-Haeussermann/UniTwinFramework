import json
import time
from .class_ComponentABC import Component
from .class_Event import Event
from pyDataverse.api import NativeApi
from pyDataverse.models import Dataverse
from pyDataverse.models import Dataset
from pyDataverse.models import Datafile
from queue import Queue
import requests
import os
import datetime
import zipfile



class class_Dataverse(Component):
    def __init__(self, _conf):
        self._event = Event()
        self._subscribers = {}
        self.Q = Queue()
        self._dataverseType = "custom"
        self._metadata = {
                           "datasetVersion": {
                              "metadataBlocks": {
                                 "citation": {
                                    "fields": [
                                       {
                                          "typeName": "title",
                                          "multiple": False,
                                          "typeClass": "primitive",
                                          "value": "Test"
                                       },
                                        {
                                            "value": [
                                                {
                                                    "authorName": {
                                                        "value": "Tim H\u00e4u\u00dfermann",
                                                        "typeClass": "primitive",
                                                        "multiple": False,
                                                        "typeName": "authorName"
                                                    },
                                                    "authorAffiliation": {
                                                        "value": "",
                                                        "typeClass": "primitive",
                                                        "multiple": False,
                                                        "typeName": "authorAffiliation"
                                                    }
                                                }
                                            ],
                                            "typeClass": "compound",
                                            "multiple": True,
                                            "typeName": "author"
                                        },
                                        {
                                            "value": [
                                                {
                                                    "datasetContactEmail": {
                                                        "typeClass": "primitive",
                                                        "multiple": False,
                                                        "typeName": "datasetContactEmail",
                                                        "value": "info@test.de"
                                                    },
                                                    "datasetContactName": {
                                                        "typeClass": "primitive",
                                                        "multiple": False,
                                                        "typeName": "datasetContactName",
                                                        "value": "Tim H\u00e4u\u00dfermann"
                                                    }
                                                }
                                            ],
                                            "typeClass": "compound",
                                            "multiple": True,
                                            "typeName": "datasetContact"
                                        },
                                       {
                                          "typeName": "dsDescription",
                                          "multiple": True,
                                          "typeClass": "compound",
                                          "value": [
                                             {
                                                "dsDescriptionValue": {
                                                   "typeName": "dsDescriptionValue",
                                                   "multiple": False,
                                                   "typeClass": "primitive",
                                                   "value": "Test"
                                                }
                                             }
                                          ]
                                       },
                                       {
                                          "typeName": "subject",
                                          "multiple": True,
                                          "typeClass": "controlledVocabulary",
                                          "value": [
                                             "Computer and Information Science"
                                          ]
                                       },
                                       {
                                          "typeName": "keywords",
                                          "multiple": True,
                                          "typeClass": "controlledVocabulary",
                                          "value": [
                                             "T1",
                                             "T2"
                                          ]
                                       },
                                       {
                                          "typeName": "productionDate",
                                          "multiple": False,
                                          "typeClass": "primitive",
                                          "value": "2022-11-17"
                                       },
                                       {
                                          "typeName": "productionPlace",
                                          "multiple": False,
                                          "typeClass": "primitive",
                                          "value": "Mannheim"
                                       },
                                       {
                                          "typeName": "dataSources",
                                          "multiple": True,
                                          "typeClass": "primitive",
                                          "value": [
                                             "Test"
                                          ]
                                       }
                                    ],
                                    "displayName": "Citation Metadata"
                                 }
                              }
                           }
                        }
        for item in _conf:
            self.__setattr__(item, _conf[item])

    def run(self):
        content = self.listDataverseContent("Unitwin", self.api_token)
        content = content["data"]
        dataset_titles = {}
        for item in content:
            if item["type"] == "dataset":
                pid = f"{item['protocol']}:{item['authority']}/{item['identifier']}"
                resp = self.curl_dataset(pid, self.api_token)
                for field in resp["data"]["latestVersion"]["metadataBlocks"]["citation"]["fields"]:
                    if field["typeName"] == "title":
                        dataset_titles[field["value"]] = pid

        if self.parent._uid not in dataset_titles:
            self.ds_pid = self.createdataset(self.api_token, "UniTwin", self.parent._uid, self.parent._uid, "UniTwin", self.mail, self.parent._uid, "Computer and Information Science")
        else:
            self.ds_pid = dataset_titles[self.parent._uid]


    def export(self):
        filename = self.Q.get()
        print(filename)
        self.uploaddatafile(self.api_token, filename, self.ds_pid)
        self._event()

    def zipfiles(self, filepath):
        with zipfile.ZipFile(filepath + ".zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(filepath):
                for file in files:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file),
                                               os.path.join(filepath, '..')))
        filepath = filepath + ".zip"
        return filepath

    def createdataverse(self, api_token, parent_dv, titel, contactEmail):
        # Set file path
        file_path = "dataverse.json"

        # set name of metadata file and import it
        try:
            with open(file_path, "r") as file:
                data = json.load(file)

        except:
            url = "https://raw.githubusercontent.com/gdcc/pyDataverse/master/tests/data/dataverse_upload_min.json"
            resp = requests.get(url)
            data = json.loads(resp.text)
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

        # Configure dataverse data
        data["alias"] = titel.translate(self.special_char_map).replace(" ", "")
        data["name"] = titel
        data["dataverseContacts"] = [{"contactEmail": contactEmail}]
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        # create Dataverse
        url = f"{self._BASE_URL}/api/dataverses/{parent_dv}"
        headers = {"X-Dataverse-key": api_token}
        resp = requests.post(url, headers=headers, data=open(file_path, 'r').read())
        print(resp.text)
        resp = resp.json()
        return resp

    def createdataset(self, api_token, dataverse, titel, author, authorAffiliation, mail, description, subject):
        # Set file path
        file_path = "dataset.json"

        if self._dataverseType == "standard":
            # set name of metadata file and import and validate it
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
            except:
                url = "https://raw.githubusercontent.com/gdcc/pyDataverse/master/tests/data/dataset_upload_min_default.json"
                resp = requests.get(url)
                data = json.loads(resp.text)
                with open("dataset.json", "w") as file:
                    json.dump(data, file, indent=4)

            # Configure dataverse data
            #data["metadataLanguage"] = "de"

            for item in data["datasetVersion"]["metadataBlocks"]["citation"]["fields"]:
                if item["typeName"] == "title":
                    item["value"] = titel
                elif item["typeName"] == "author":
                    for subitem in item["value"]:
                        subitem["authorName"]["value"] = author
                        subitem["authorAffiliation"]["value"] = authorAffiliation
                elif item["typeName"] == "datasetContact":
                    for subitem in item["value"]:
                        subitem["datasetContactEmail"]["value"] = mail
                        subitem["datasetContactName"]["value"] = author
                elif item["typeName"] == "dsDescription":
                    for subitem in item["value"]:
                        subitem["dsDescriptionValue"]["value"] = description
                elif item["typeName"] == "subject":
                    item["value"] = [subject]
            print(data)

        elif self._dataverseType == "custom":
            # set name of metadata file and import and validate it
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
            except:
                data = self._metadata

            # Configure dataverse data
            # data["metadataLanguage"] = "de"

            for item in data["datasetVersion"]["metadataBlocks"]["citation"]["fields"]:
                if item["typeName"] == "title":
                    item["value"] = titel
                elif item["typeName"] == "author":
                    for subitem in item["value"]:
                        subitem["authorName"]["value"] = author
                        subitem["authorAffiliation"]["value"] = authorAffiliation
                elif item["typeName"] == "datasetContact":
                    for subitem in item["value"]:
                        subitem["datasetContactEmail"]["value"] = mail
                        subitem["datasetContactName"]["value"] = author
                elif item["typeName"] == "dsDescription":
                    for subitem in item["value"]:
                        subitem["dsDescriptionValue"]["value"] = description
                elif item["typeName"] == "subject":
                    item["value"] = [subject]
                elif item["typeName"] == "productionDate":
                    item["value"] = datetime.datetime.today().strftime('%Y-%m-%d')
                # elif item["typeName"] == "dataSources":
                #     item["value"] = [author]

        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        # create dataset
        url = f"{self._BASE_URL}/api/dataverses/{dataverse}/datasets"
        headers = {"X-Dataverse-key": api_token}
        with open('dataset.json', 'r') as f:
            data = f.read()
        # resp = requests.post(url, headers=headers, data=open(file_path, 'r').read(), verify=False)
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp = resp.json()
        print(resp)
        return resp["data"]["persistentId"]

    def uploaddatafile(self, api_token, filepath, ds_pid):
        url = f"{self._BASE_URL}/api/datasets/:persistentId/add"
        headers = {"X-Dataverse-key": api_token}
        params = {"persistentId": ds_pid}

        # upload datafile
        if os.path.isdir(filepath):
            print("\nIt is a directory")
            filepath = self.zipfiles(filepath)
        elif os.path.isfile(filepath):
            print("\nIt is a normal file")
        else:
            print("It is a special file (socket, FIFO, device file)")
        files = {"file": open(filepath, "rb"), "jsonData": (None, '{"categories":["Data"], "restrict":"false", "tabIngest":"false"}')}
        resp = requests.post(url, headers=headers, params=params, files=files, verify=False)
        resp = resp.json()
        print(resp)

        # get reference
        resp = self.curl_dataset(ds_pid, api_token)
        reference = {"DOI": ds_pid, "dataverseURL": f"{self._BASE_URL}/dataset.xhtml?persistentId={ds_pid}", "persistentURL": resp["data"]["persistentUrl"]}
        self.parent._references[filepath] = reference
        return reference

    def listDataverses(self):
        dataverseList = []
        resp = requests.get(self._BASE_URL + "/api/dataverses/" + self._rootDataverse + "/contents")
        resp = resp.json()

        for item in resp:
            if item == "data":
                for subitem in resp[item]:
                    if subitem["type"] == "dataverse":
                        dataverseList.append({"name": subitem["title"], "id": subitem["id"]})

        for dataverse in dataverseList:
            resp = requests.get(self._BASE_URL + "/api/dataverses/" + str(dataverse["id"]) + "/contents")
            resp = resp.json()
            for item in resp:
                if item == "data":
                    for subitem in resp[item]:
                        if subitem["type"] == "dataverse":
                            dataverseList.append({"name": subitem["title"], "id": subitem["id"]})
        return dataverseList

    def listDataverseContent(self, dataverse_id, api_token):
        url = f"{self._BASE_URL}/api/dataverses/{dataverse_id}/contents"
        headers = {
            'X-Dataverse-key': api_token
        }
        response = requests.get(url, headers=headers, verify=False).json()
        return response

    def curl_dataset(self, dataset_pid, api_token):
        url = f"{self._BASE_URL}/api/datasets/:persistentId/?persistentId={dataset_pid}"
        headers = {
            'X-Dataverse-key': api_token
        }
        response = requests.get(url, headers=headers, verify=False).json()
        print(response)
        return response

