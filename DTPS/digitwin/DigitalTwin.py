import datetime
import datetime as dt
import uuid
from bson.objectid import ObjectId
from marshmallow import Schema, fields, post_load


class DigitalTwin:
    """
    A class to represent a digital twin. At this point in time,
    the digital twin only consists of a unique id (which is auto-generated
    or loaded from the persistence engine) as well as a creation date.
    Only properties are persisted, no methods or code.
    The name of the _id-Property is chosen because it's also the name of
    the unique identifier of 01-dt-db_mongodb which is used as persistence layer in
    this context (thus generating almost zero overhead inside the
    serializer).
    """

    def __init__(self, created_at : datetime.datetime = None, _id: str = None):
        self._id = _id or uuid.uuid4().hex
        self.created_at = created_at or dt.datetime.now()

    def __str__(self):
        return str(self._id)

    def say_hello(self):
        print("Hello from %s" % self._id)


class DigitalTwinSchema(Schema):
    """
    A schema representation of a digital twin (which represents
    only the properties, no methods) which is derived from the
    Schema class of the marshmallow-package.
    """
    _id = fields.Str()   # _id
    created_at = fields.DateTime()

    @post_load
    def make_twin(self, data, **kwargs):
        return DigitalTwin(**data)

