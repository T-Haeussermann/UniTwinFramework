import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from minio import Minio
from .class_ComponentABC import Component
from .class_Event import Event


class class_Minio(Component):
    def __init__(self, _conf):
        self._event = Event()

        # add route to server file
        self._router = APIRouter()
        self._router.add_api_route("/server_file/{file}", self.server_file, methods=["GET"])

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self._client = Minio(endpoint=self._endpoint, access_key=self._access_key, secret_key=self._secret_key, secure=False)

    def upload(self, name):
        result = self._client.fput_object(bucket_name=self._bucket_name, object_name=name, file_path=name)
        self.parent._references[name] ={"object_name": name,
                                        "path": f"{self._endpoint}/{self._bucket_name}/{name}"}
        print(result)

    def download(self, name):
        object_name = self.parent._references[name]["object_name"]
        result = self._client.fget_object(bucket_name=self._bucket_name, object_name=object_name, file_path=object_name)
        print(result)

    def server_file(self, name):
        object_name = self.parent._references[name]["object_name"]
        data = self._client.get_object(self._bucket_name, object_name).read()
        print(data)
        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")

    def run(self):
        self.newBucket()
    def newBucket(self):
        self._bucket_name = self.parent._uid
        if self._client.bucket_exists(self._bucket_name):
            print("Minio bucket already exists. Doing nothing!")
        else:
            self._client.make_bucket(self._bucket_name)

{
    "class_Minio": {
        "I1": {
            "_id": "class_Minio",
            "_endpoint": "os-svc.dt.svc.cluster.local:9000",
            "_access_key": "minio",
            "_secret_key": "minio123"
        }
    }
}