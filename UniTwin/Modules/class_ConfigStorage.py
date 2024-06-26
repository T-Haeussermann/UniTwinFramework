from .class_ComponentABC import Component
import urllib.parse
from pymongo import MongoClient
class class_ConfigStorage(Component):
    def __init__(self):
        self._id = "ConfigStorage"
        self.username = urllib.parse.quote_plus("dt")
        self.password = urllib.parse.quote_plus("dt")
        self._uri = "mongodb://" + self.username + ":" + self.password + "@cs-svc.dt.svc.cluster.local:27018/confTwins?authSource=admin&authMechanism=SCRAM-SHA-256"
        self.myclient = MongoClient(self._uri)
        # database
        self.db = self.myclient.get_database(name="confTwins")
        # Created or Switched to collection
        self.Collection = self.db["conf"]

    def query(self, myquery):
        mydoc = self.Collection.find_one(myquery)
        return mydoc