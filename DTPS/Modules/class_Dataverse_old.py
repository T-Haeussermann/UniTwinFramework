import json
import time
from .class_ComponentABC import Component
from .class_Event import Event
from pyDataverse.api import NativeApi
from pyDataverse.models import Dataverse
from pyDataverse.models import Dataset
from pyDataverse.models import Datafile
from pyDataverse.utils import read_file
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.observers.polling import PollingObserver
from queue import Queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import os
import zipfile


class class_Dataverse_old(Component):
    def __init__(self, _conf):
        self._event = Event()
        self._subscribers = {}
        self.Q = Queue()
        self.path = "./watch"
        self.filePath = ""

        for item in _conf:
            self.__setattr__(item, _conf[item])
        # self.api = NativeApi(self._BASE_URL, self._API_TOKEN)
        self.root = None
        self.apiToken = None
        self.listboxDV = None
        self.scrollbarDV = None
        self.var = None
        self.dataset_list_label = None
        self.listboxDS = None
        self.scrollbarDS = None
        self.dataset_entry = None
        self.Dataverse = None
        self.Dataset = None
        self.DatasetList = None
        self.dataset_label = None

        # create dir if not present
        self.createDir()
        self.documents = dict()  # key = document label   value = Document reference

        # # add code for mounting path to watch in /watch
        # requests.get("http://dtps-svc.dt.svc.cluster.local:8000/mount/" + self.parent._uid + "/" + self._dir)

        self.event_handler = LoggingEventHandler()   #FileSystemEventHandler()
        self.event_handler.on_any_event = self.on_any_event
        self.event_handler.on_created = self.on_created
        self.observer = PollingObserver() #Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=False)

    def run(self):
        print(self._parent)
        requests.get("http://dtps-svc.dt.svc.cluster.local:8000/mount/" + self._parent._uid + "/" + self._dir)
        self.observer.start()
    def createDir(self):
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def on_any_event(self, event):
        print(event.src_path, event.event_type)
    def on_created(self, event):
        print("created: " + event.src_path)
        # if ".zip" not in event.src_path:
        if event.src_path not in self.filePath:
            self.filePath = event.src_path
            self.gui()


    def createdataverse(self):
        # create pyDataverse object
        dv = Dataverse()

        # set name of metadata file and import it
        dv_filename = "dataverse.json"
        dv.from_json(read_file(dv_filename))

        # create Dataverse
        self.api.create_dataverse("Sub-Test-Dataverse", dv.json())

    def createdataset(self, titel):
        self.api = NativeApi(self._BASE_URL, self.api_token)
        # create empty pyDataverse Object
        ds = Dataset()

        # set name of metadata file and import and validate it
        try:
            ds_filename = "dataset.json"
            ds.from_json(read_file(ds_filename))
        except:
            url = "https://raw.githubusercontent.com/gdcc/pyDataverse/master/tests/data/user-guide/dataset.json"
            resp = requests.get(url)
            data = json.loads(resp.text)
            print(data)
            with open("dataset.json", "w") as file:
                json.dump(data, file)
            ds_filename = "dataset.json"
            ds.from_json(read_file(ds_filename))

        # change title
        ds.set({"title": titel})

        # create dataset
        for item in self.dataverseList:
            if item["name"] == self.dataverse:
                id = item["id"]
                print(item)
        resp = self.api.create_dataset(id, ds.json())
        resp = resp.json()
        return resp["data"]["persistentId"]

    def uploaddatafile(self, ds_pid):
        self.api = NativeApi(self._BASE_URL, self.api_token)
        # create empty pyDataverse Object
        df = Datafile()

        # set filename and pid of Dataset
        df.set({"pid": ds_pid, "filename": self.filePath})
        df.get()

        # upload datafile
        if os.path.isdir(self.filePath):
            print("\nIt is a directory")
            self.zipfiles()
            resultUP = self.api.upload_datafile(ds_pid, self.filePath, df.json()).json()
            os.remove(self.filePath)
        elif os.path.isfile(self.filePath):
            print("\nIt is a normal file")
            resultUP = self.api.upload_datafile(ds_pid, self.filePath, df.json()).json()
        else:
            print("It is a special file (socket, FIFO, device file)")

        # get reference
        result = self.api.get_dataset(ds_pid).json()
        reference = {"Dataverse Dataset": {"FileName": resultUP["data"]["files"][0]["label"], "DOI": ds_pid, "URL": result["data"]["persistentUrl"]}}
        self.parent._references.append(reference)


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
        self.dataverseList = dataverseList
        return dataverseList

    def zipfiles(self):
        with zipfile.ZipFile(self.filePath + ".zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.filePath):
                for file in files:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file),
                                               os.path.join(self.filePath, '..')))
        print(self.filePath)
        self.filePath = self.filePath + ".zip"
        print(self.filePath)

    def gui(self):
        self.root = tk.Tk()
        self.root.title("New Data Form")
        self.root.geometry("400x300")

        # create variables to store the input values
        self.apiToken = tk.StringVar()
        self.Dataverse = tk.StringVar()
        self.Dataset = tk.StringVar()
        self.DatasetList = tk.StringVar()
        self.var = tk.BooleanVar()
        # create the form elements

        # api token text input
        tk.Label(self.root, text="API Token:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.apiToken, font=("Helvetica", 12)).grid(row=0, column=1, padx=10, pady=10)

        # listbox for dataverse selection
        tk.Label(self.root, text="Dataverse:", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=5)
        self.scrollbarDV = ttk.Scrollbar(self.root, orient="vertical")
        self.scrollbarDV.grid(row=1, column=3, padx=10, pady=5)
        self.listboxDV = tk.Listbox(self.root, font=("Helvetica", 12), height=2, exportselection=0)
        for idx, item in enumerate(self.listDataverses()):
            self.listboxDV.insert(idx, item["name"])
        self.listboxDV.grid(row=1, column=1, padx=10, pady=5)

        self.listboxDV.config(yscrollcommand=self.scrollbarDV.set)
        # Configure the scrollbar
        self.scrollbarDV.config(command=self.listboxDV.yview)

        # check box for new dataset or existing
        self.var.set(False)
        tk.Checkbutton(self.root, text="Create New Dataset", variable=self.var, font=("Helvetica", 12),
                       command=self.toggle_dataset).grid(row=2, column=1, padx=10, pady=5)

        # dataset textinput for new dataset
        self.dataset_label = tk.Label(self.root, text="Dataset:", font=("Helvetica", 12))
        self.dataset_entry = tk.Entry(self.root, textvariable=self.Dataset, font=("Helvetica", 12))
        self.dataset_label.grid(row=4, column=0, padx=10, pady=5)
        self.dataset_entry.grid(row=4, column=1, padx=10, pady=5)


        # dataset list
        self.dataset_list_label = tk.Label(self.root, text="Datasets:", font=("Helvetica", 12))
        self.dataset_list_label.grid(row=4, column=0, padx=10, pady=5)

        # second Listbox causes problem
        # #
        self.scrollbarDS = ttk.Scrollbar(self.root, orient="vertical")
        self.scrollbarDS.grid(row=4, column=3, padx=10, pady=5)
        self.listboxDS = tk.Listbox(self.root, font=("Helvetica", 12), height=2, exportselection=0)

        self.listboxDS.grid(row=4, column=1, padx=10, pady=5)

        self.listboxDS.config(yscrollcommand=self.scrollbarDS.set)
        # Configure the scrollbar
        self.scrollbarDS.config(command=self.listboxDS.yview)


        # center the form elements and labels in the form
        for i in range(7):
            self.root.grid_rowconfigure(i, weight=1)
            self.root.grid_columnconfigure(i, weight=1)

        # center the form elements in their respective cells
        for child in self.root.winfo_children():
            child.grid_configure(padx=5, pady=5, sticky="nsew")

        # center the labels in their respective cells
        for label in self.root.grid_slaves():
            if isinstance(label, tk.Label):
                label.grid_configure(sticky="nsew")

        # hide the Dataset input by default
        self.dataset_label.grid_remove()
        self.dataset_entry.grid_remove()

        # create the search button
        tk.Button(self.root, text="Search", command=self.search, font=("Helvetica", 12)).grid(row=3, column=1, pady=10)

        # create the submit button
        tk.Button(self.root, text="Submit", command=self.submit, font=("Helvetica", 12)).grid(row=5, column=1, pady=10)

        self.root.mainloop()
    def toggle_dataset(self):
        # show/hide the DatasetList input based on the value of the create_new_dataset variable
        if self.var.get():
            self.dataset_list_label.grid_remove()
            self.listboxDS.grid_remove()
            self.scrollbarDS.grid_remove()
            self.dataset_label.grid()
            self.dataset_entry.grid()
        else:
            self.dataset_list_label.grid()
            self.listboxDS.grid()
            self.scrollbarDS.grid()
            self.dataset_label.grid_remove()
            self.dataset_entry.grid_remove()

    def search(self):
        if self.var.get():
            pass
        else:
            if self.apiToken.get() == "":
                messagebox.showerror("Error", "API Token is missing. Please provide a valid API Token.")
            elif self.listboxDV.curselection() == ():
                messagebox.showerror("Error", "No Dataverse selected. Please select one.")
            else:
                newList = []
                self.datasetWithPID = []
                self.listboxDS.delete(0, tk.END)

                for item in self.listboxDV.curselection():
                    self.dataverse = self.listboxDV.get(item)
                dataverses = self.listDataverses()
                for item in dataverses:
                    if item["name"] == self.dataverse:
                        datasetList = []
                        resp = requests.get(self._BASE_URL + "/api/dataverses/" + str(item["id"]) + "/contents")
                        resp = resp.json()
                        for subitem in resp:
                            if subitem == "data":
                                for subsubitem in resp[subitem]:
                                    if subsubitem["type"] == "dataset":
                                        datasetList.append(subsubitem)
                headers = {"X-Dataverse-key": self.apiToken.get()}

                for item in datasetList:
                    persistentUrl = item["persistentUrl"]
                    persistentUrl = persistentUrl.replace("https://doi.org/", "")
                    resp = requests.get(f"{self._BASE_URL}/api/datasets/:persistentId" + "/?persistentId=doi:" + str(persistentUrl), headers=headers)
                    resp = resp.json()
                    newitem = (resp["data"]["latestVersion"]["metadataBlocks"]["citation"]["fields"][0]["value"])
                    self.datasetWithPID.append({"name": newitem, "pid": "doi:" + persistentUrl})
                    newList.append(newitem)
                print(self.datasetWithPID)
                print(datasetList)
                print(newList)
                for idx, item in enumerate(newList):
                    self.listboxDS.insert(idx, item)

    def submit(self):
        # code to handle form submission
        # you can access the input values using apiToken.get() for the text inputs
        # and var.get() for the yes/no question
        self.api_token = self.apiToken.get()
        # self.dataverse = self.listbox.get()   #self.Dataverse.get()
        for item in self.listboxDV.curselection():
            self.dataverse = self.listboxDV.get(item)
        self.create_new_dataset = self.var.get()

        print("api_token: " + str(self.api_token))
        print("dataverse: " + str(self.dataverse))
        print("create_new_dataset: " + str(self.create_new_dataset))
        if self.create_new_dataset == True:
            self.dataset = self.Dataset.get()
            pid = self.createdataset(titel=self.dataset)
            self.uploaddatafile(pid)
            print("dataset: " + str(self.dataset))
        else:
            for item in self.listboxDS.curselection():
                self.dataset = self.listboxDS.get(item)
                for item in self.datasetWithPID:
                    if item["name"] == self.dataset:
                        pid = item["pid"]
                self.uploaddatafile(pid)
                print("dataset: " + str(self.dataset))

        if self.api_token != "" and self.dataverse != "" and self.dataset != "":
            # close the form
            self.root.destroy()
        else:
            pass

