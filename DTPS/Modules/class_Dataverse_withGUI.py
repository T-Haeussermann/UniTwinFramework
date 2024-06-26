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


class class_Dataverse_withGUI(Component):
    def __init__(self, _conf):
        self._event = Event()
        self._subscribers = {}
        self.Q = Queue()
        self.path = "./watch"
        self.filePath = ""

        for item in _conf:
            self.__setattr__(item, _conf[item])
        self.root = None
        self.apiToken = None
        self.listboxDV = None
        self.var = None
        self.dataset_list_label = None
        self.listboxDS = None
        self.dataset_entry = None
        self.Dataverse = None
        self.Dataset = None
        self.Datasets = []
        self.DatasetList = None
        self.dataset_label = None


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
        data["metadataLanguage"] = "de"

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
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        # create dataset
        for item in self.listDataverses():
            if item["name"] == dataverse:
                id = item["id"]
                print(item)
        url = f"{self._BASE_URL}/api/dataverses/{id}/datasets"
        headers = {"X-Dataverse-key": api_token}
        with open('dataset.json', 'rb') as f:
            data = f.read()
        resp = requests.post(url, headers=headers, data=open(file_path, 'r').read())
        print(resp.text)
        resp = resp.json()
        return resp["data"]["persistentId"]

    def uploaddatafile(self, api_token, filepath, ds_pid):
        #Create API instance
        api = NativeApi(self._BASE_URL, api_token)

        # create empty pyDataverse Object
        df = Datafile()

        # set filename and pid of Dataset
        df.get()
        df.set({"pid": ds_pid, "filename": filepath})

        print(filepath)
        # upload datafile
        if os.path.isdir(filepath):
            print("\nIt is a directory")
            filepath = self.zipfiles(filepath)
            resultUP = api.upload_datafile(ds_pid, filepath, df.json()).json()
            os.remove(filepath)
        elif os.path.isfile(filepath):
            print("\nIt is a normal file")
            resultUP = api.upload_datafile(ds_pid, filepath, df.json()).json()
        else:
            print("It is a special file (socket, FIFO, device file)")

        # get reference
        result = api.get_dataset(ds_pid).json()
        reference = {"Dataverse Dataset": {"FileName": resultUP["data"]["files"][0]["label"], "DOI": ds_pid,
                                           "URL": result["data"]["persistentUrl"]}}
        self.parent._references[self.filePath] = reference
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

    def zipfiles(self, filepath):
        with zipfile.ZipFile(filepath + ".zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(filepath):
                for file in files:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file),
                                               os.path.join(filepath, '..')))
        filepath = filepath + ".zip"
        return filepath

    def gui(self):
        # Get file path
        self.filePath = self.Q.get()

        # create gui
        self.root = tk.Tk()
        self.root.title("New Data Upload Form")
        self.root.geometry("700x300")

        # create variables to store the input values
        self.apiToken = tk.StringVar()
        self.Dataverse = tk.StringVar()
        self.Dataset = tk.StringVar()
        self.DatasetList = tk.StringVar()
        self.var = tk.BooleanVar()

        # create variables to store the input values for new dataset
        self.Author = tk.StringVar()
        self.AuthorAffiliation = tk.StringVar()
        self.Email = tk.StringVar()
        self.Description = tk.StringVar()
        self.Subject = tk.StringVar()

        # api token text input
        tk.Label(self.root, text="API Token:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(self.root, textvariable=self.apiToken, font=("Helvetica", 12)).grid(row=0, column=1, padx=10, pady=5)

        # dataverse selection via dropdown
        tk.Label(self.root, text="Dataverse:", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=5)
        # extract available dataverses
        dataverses = []
        for item in self.listDataverses():
            dataverses.append(item["name"])
        self.listboxDV = tk.OptionMenu(self.root, self.Dataverse, *dataverses)
        self.listboxDV.config(font=("Helvetica", 12))
        self.listboxDV.grid(row=1, column=1, padx=10, pady=5)

         # check box for new dataset or existing
        self.var.set(False)
        tk.Checkbutton(self.root, text="Create New Dataset", variable=self.var, font=("Helvetica", 12),
                       command=self.toggle_dataset).grid(row=2, column=1, padx=10, pady=5)

        # dataset textinput for new dataset
        self.dataset_label = tk.Label(self.root, text="Dataset:", font=("Helvetica", 12))
        self.dataset_entry = tk.Entry(self.root, textvariable=self.Dataset, font=("Helvetica", 12))
        self.dataset_label.grid(row=4, column=0, padx=10, pady=5)
        self.dataset_entry.grid(row=4, column=1, padx=10, pady=5)

        self.author_label = tk.Label(self.root, text="Author:", font=("Helvetica", 12))
        self.author_entry = tk.Entry(self.root, textvariable=self.Author, font=("Helvetica", 12))
        self.author_label.grid(row=6, column=0, padx=10, pady=5)
        self.author_entry.grid(row=6, column=1, padx=10, pady=5)

        self.affiliation_label = tk.Label(self.root, text="Author Affiliation:", font=("Helvetica", 12))
        self.affiliation_entry = tk.Entry(self.root, textvariable=self.AuthorAffiliation, font=("Helvetica", 12))
        self.affiliation_label.grid(row=7, column=0, padx=10, pady=5)
        self.affiliation_entry.grid(row=7, column=1, padx=10, pady=5)

        self.email_label = tk.Label(self.root, text="Email (info@mail.de):", font=("Helvetica", 12))
        self.email_entry = tk.Entry(self.root, textvariable=self.Email, font=("Helvetica", 12))
        self.email_label.grid(row=8, column=0, padx=10, pady=5)
        self.email_entry.grid(row=8, column=1, padx=10, pady=5)

        self.description_label = tk.Label(self.root, text="Description:", font=("Helvetica", 12))
        self.description_entry = tk.Entry(self.root, textvariable=self.Description, font=("Helvetica", 12))
        self.description_label.grid(row=9, column=0, padx=10, pady=5)
        self.description_entry.grid(row=9, column=1, padx=10, pady=5)

        self.subject_label = tk.Label(self.root, text="Subject:", font=("Helvetica", 12))
        # Create a list of subject options
        subjects = [
            "Agricultural Sciences",
            "Arts and Humanities",
            "Astronomy and Astrophysics",
            "Business and Management",
            "Chemistry",
            "Computer and Information Science",
            "Earth and Environmental Sciences",
            "Engineering",
            "Law",
            "Mathematical Sciences",
            "Medicine, Health and Life Sciences",
            "Physics",
            "Social Sciences",
            "Other"
        ]
        self.subject_entry = tk.OptionMenu(self.root, self.Subject, *subjects)
        self.subject_entry.config(font=("Helvetica", 12))
        self.subject_label.grid(row=10, column=0, padx=10, pady=5)
        self.subject_entry.grid(row=10, column=1, padx=10, pady=5)

        # dataset selection via dropdown
        self.dataset_list_label = tk.Label(self.root, text="Datasets:", font=("Helvetica", 12))
        self.dataset_list_label.grid(row=4, column=0, padx=10, pady=5)
        self.listboxDS = tk.OptionMenu(self.root, self.Dataset, self.Datasets)
        self.listboxDS.config(font=("Helvetica", 12))
        self.listboxDS.grid(row=4, column=1, padx=10, pady=5)

        # hide the Dataset input by default
        self.dataset_label.grid_remove()
        self.dataset_entry.grid_remove()
        self.author_label.grid_remove()
        self.author_entry.grid_remove()
        self.affiliation_label.grid_remove()
        self.affiliation_entry.grid_remove()
        self.email_label.grid_remove()
        self.email_entry.grid_remove()
        self.description_label.grid_remove()
        self.description_entry.grid_remove()
        self.subject_label.grid_remove()
        self.subject_entry.grid_remove()

        # create the search button
        tk.Button(self.root, text="Search", command=self.search, font=("Helvetica", 12)).grid(row=3, column=1, pady=10)

        # create the submit button
        tk.Button(self.root, text="Submit", command=self.submit, font=("Helvetica", 12)).grid(row=5, column=1, pady=10)

        self.root.mainloop()

    def toggle_dataset(self):
        # show/hide the DatasetList input based on the value of the create_new_dataset variable
        if self.var.get():
            self.root.geometry("700x600")
            self.dataset_list_label.grid_remove()
            self.listboxDS.grid_remove()
            self.dataset_label.grid()
            self.dataset_entry.grid()

            #addition
            self.author_label.grid()
            self.author_entry.grid()
            self.affiliation_label.grid()
            self.affiliation_entry.grid()
            self.email_label.grid()
            self.email_entry.grid()
            self.description_label.grid()
            self.description_entry.grid()
            self.subject_label.grid()
            self.subject_entry.grid()

        else:
            self.root.geometry("700x300")
            self.dataset_list_label.grid()
            self.listboxDS.grid()
            self.dataset_label.grid_remove()
            self.dataset_entry.grid_remove()

            #addition
            self.author_label.grid_remove()
            self.author_entry.grid_remove()
            self.affiliation_label.grid_remove()
            self.affiliation_entry.grid_remove()
            self.email_label.grid_remove()
            self.email_entry.grid_remove()
            self.description_label.grid_remove()
            self.description_entry.grid_remove()
            self.subject_label.grid_remove()
            self.subject_entry.grid_remove()

    def search(self):
        if self.var.get():
            pass
        else:
            if self.apiToken.get() == "":
                messagebox.showerror("Error", "API Token is missing. Please provide a valid API Token.")
            elif self.Dataverse.get() == "":
                messagebox.showerror("Error", "No Dataverse selected. Please select one.")
            else:
                newList = []
                self.datasetWithPID = []
                #self.listboxDS.delete(0, tk.END)

                dataverses = self.listDataverses()
                print(dataverses)
                for item in dataverses:
                    if item["name"] == self.Dataverse.get():
                        datasetList = []
                        resp = requests.get(self._BASE_URL + "/api/dataverses/" + str(item["id"]) + "/contents")
                        resp = resp.json()
                        print(resp)
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
                    self.Datasets.append((item))
                    # self.listboxDS.
                    # self.listboxDS.insert(idx, item)


    def submit(self):
        # code to handle form submission
        # you can access the input values using apiToken.get() for the text inputs
        # and var.get() for the yes/no question
        self.api_token = self.apiToken.get()
        # self.dataverse = self.listbox.get()   #self.Dataverse.get()
        for item in self.listboxDV.curselection():
            self.dataverse = self.listboxDV.get(item)
        self.create_new_dataset = self.var.get()

        # Get values of inputs
        self.Author = self.Author.get()
        self.AuthorAffiliation = self.AuthorAffiliation.get()
        self.Email = self.Email.get()
        self.Description = self.Description.get()
        self.Subject = self.Subject.get()

        print("api_token: " + str(self.api_token))
        print("dataverse: " + str(self.dataverse))
        print("create_new_dataset: " + str(self.create_new_dataset))
        if self.create_new_dataset == True:
            self.dataset = self.Dataset.get()
            pid = self.createdataset(self.api_token, self.dataverse, self.dataset, self.Author, self.AuthorAffiliation,
                                     self.Email, self.Description, self.Subject)
            self.uploaddatafile(self.api_token, self.filePath, pid)
            print("dataset: " + str(self.dataset))
        else:
            for item in self.listboxDS.curselection():
                self.dataset = self.listboxDS.get(item)
                for item in self.datasetWithPID:
                    if item["name"] == self.dataset:
                        pid = item["pid"]
                self.uploaddatafile(self.api_token, self.filePath, pid)
                print("dataset: " + str(self.dataset))

        if self.api_token != "" and self.dataverse != "" and self.dataset != "":
            # close the form
            self.root.destroy()
        else:
            pass

