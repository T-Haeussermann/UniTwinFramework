import pymongo


class MongoDTSerializer:

    _user = "dt"
    _pwd = "dt"

    @classmethod
    def initialize(cls):
        # basic
        # client = pymongo.MongoClient("mongodb://%s:%s@localhost:27017/digitalTwins" % (cls._user, cls._pwd))
        #kubernetes
        uri = "mongodb://" + cls._user + ":" + cls._pwd + "@dt-db-svc.dt.svc.cluster.local:27017/digitalTwins?authSource=admin&authMechanism=SCRAM-SHA-256"
        client = pymongo.MongoClient(uri)
        pymongo.MongoClient()
        cls.database = client.get_database()

    @classmethod
    def persist(cls, data):
        cls.database.twins.insert_one(data)

    @classmethod
    def load_twin(cls, _id):
        return cls.database.twins.find_one({"_id": _id})
