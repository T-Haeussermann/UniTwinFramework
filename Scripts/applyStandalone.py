import docker

client = docker.from_env()

conf = '{"class_MQTT":{"I1":{"_id":"class_MQTT-I1","_username":"dbt","_passwd":"dbt","_host":"mq.jreichwald.de","_port":1883,"_topic_sub":["Topic1","Topic2","Measurement"],"_subscribers":{"method_MQTT-I1":"method_MQTT"},"_subscriptions":{}}},"method_MQTT":{"I1":{"_id":"method_MQTT-I1","_subscribers":{},"_subscriptions":{}}}}'
uid = "123456789"
image = "unitwin_standalone:1.0"
environment_variables = {"UID": uid, "STANDALONE": True, "CONFIGURATION": conf}
ports = {"7000/tcp": 7000}

client.containers.run(image=image, detach=True, environment=environment_variables, ports=ports)