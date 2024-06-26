import pymongo


class MongoConfSerializer:

    _user = "dt"
    _pwd = "dt"

    @classmethod
    def initialize(cls):
        # basic
        # client = pymongo.MongoClient("mongodb://%s:%s@localhost:27017/digitalTwins" % (cls._user, cls._pwd))
        # kubernetes
        uri = "mongodb://" + cls._user + ":" + cls._pwd + "@cs-svc.dt.svc.cluster.local:27018/confTwins?authSource=admin&authMechanism=SCRAM-SHA-256"
        client = pymongo.MongoClient(uri)
        pymongo.MongoClient()
        cls.database = client.get_default_database()

    @classmethod
    def persist(cls, data):
        cls.database.conf.insert_one(data)

    @classmethod
    def load_twin(cls, _id):
        return cls.database.conf.find_one({"_id": _id})

    @classmethod
    def delete_conf(cls, _id):
        cls.database.conf.delete_one({"_id": _id})
