import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from .class_ComponentABC import Component
from .class_Event import Event

class class_Influxdb(Component):
    def __init__(self, _conf):
        self._event = Event()

        for item in _conf:
            self.__setattr__(item, _conf[item])
        # self.retention_rules = BucketRetentionRules(type="expire", every_seconds=86400) #Bei Bedarf ausfüllen

    @property
    def dbclient(self):
        return InfluxDBClient(url=self._url, token=self._token, org=self._org)

    @property
    def buckets_api(self):
        return self.dbclient.buckets_api()

    @property
    def write_api(self):
        return self.dbclient.write_api(write_options=SYNCHRONOUS)

    def write(self, bucket, item, value, unit=None):
        if unit is not None:
            point = Point("Measurement").tag("Sensor", item).field("Value", value).tag("Unit", unit)
        else:
            point = Point("Measurement").tag("Sensor", item).field("Value", value)
        self.write_api.write(bucket=bucket, org=self._org, record=point)
        for subscriber in self._subscribers:
            subscriber = self.parent.getChild(subscriber)
            subscriber.Q.put({"Sensor": item, "Value": value})
        self._event()

    def new_Bucket(self, Name):
        if self.buckets_api.find_bucket_by_name(bucket_name=Name) is None:
            self.buckets_api.create_bucket(bucket_name=Name, retention_rules=None, org=self._org)
        else:
            pass

    def run(self):
        # create bucket with uid on instantiation
        self.new_Bucket(self.parent._uid)


    def query(self, bucket, format="data_frame", time=10, last=False):
        if last == False:
            query = f'''from(bucket: "{bucket}")
                      |> range(start: -{str(time)}s)
                      |> filter(fn: (r) => r["_measurement"] == "Measurement")
                      |> filter(fn: (r) => r["_field"] == "Value")
                      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'''

        elif last == True:
            query = f'''from(bucket: "{bucket}")
                        |> range(start: -{str(time)}s)
                        |> filter(fn: (r) => r["_measurement"] == "Measurement")
                        |> filter(fn: (r) => r["_field"] == "Value")
                        |> last()
                        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'''

        if format == "data_frame":
            return self.dbclient.query_api().query_data_frame(query, self._org)
        elif format == "csv":
            return self.dbclient.query_api().query_csv(query, self._org)
        elif format == "influx":
            return self.dbclient.query_api().query(query, self._org)
