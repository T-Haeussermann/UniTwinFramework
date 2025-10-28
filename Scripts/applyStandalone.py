import docker
import json

client = docker.from_env()

conf_file = "conf_standalone.json"
uid = "123456789"
image = "unitwin_standalone:1.0"
environment_variables = {"UID": uid, "STANDALONE": True, "CONFIGURATION": conf}
ports = {"7000/tcp": 7000}

with open(file=conf_file, mode="r") as file:
    conf = json.load(file)

client.containers.run(image=image, detach=True, environment=environment_variables, ports=ports)
