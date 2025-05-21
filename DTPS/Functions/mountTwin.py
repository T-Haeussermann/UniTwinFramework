from kubernetes import client, config
from kubernetes.client.models import (
    V1DeploymentSpec,
    V1LabelSelector, V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1Container,
    V1ContainerPort,
    V1EnvVar,
    V1Volume,
    V1HostPathVolumeSource,
    V1VolumeMount)

def mountTwin(definition, path):

    # Define the Kubernetes API client
    api_client = definition["api_client"]
    api_instance = client.AppsV1Api(api_client)

    # Define the namespace for the deployment, service, and ingress
    namespace = definition["namespace"]

    # Define the name for the deployment
    name = definition["name"]
    volume_name = name

    # Define path for windows machines
    if "\\" in path:
        path = path.replace("C:\\", "")
        path = "/run/desktop/mnt/host/c/" + path.replace("\\", "/")
    print(path)

    # get deployment
    deployment = api_instance.read_namespaced_deployment(name=name, namespace=namespace)

    if deployment.spec.template.spec.containers[0].volume_mounts == None:
        # define mount volume
        mount_volume = V1VolumeMount(mount_path="UniTwin/watch", name=volume_name)
        deployment.spec.template.spec.containers[0].volume_mounts = [mount_volume]

        # define deployment volume, be aware on windows add /run/desktop/mnt/host/c/ befor path
        volume = V1Volume(
            name=volume_name,
            host_path=V1HostPathVolumeSource(
                path=path)
        )
        deployment.spec.template.spec.volumes = [volume]

        # update deployment
        resp = api_instance.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)

    else:
        resp = "Already mounted"

    return {definition["uid"]: resp}



# # variables
# name = "dt-0139e71cb4084bf2a91be61fe8d034b6"
# namespace = "dt"
# volume_name = name
# # Load the Kubernetes configuration
# config.load_kube_config()
#
# # Define the Kubernetes API client
# api = client.CoreV1Api()
#
# # Define the AppsV1 API client
# api_instance = client.AppsV1Api()
#
#
# # get deployment
# deployment = api_instance.read_namespaced_deployment(name=name, namespace=namespace)
#
# # define mount volume
# mount_volume = V1VolumeMount(mount_path="UniTwin/watch", name=volume_name)
# deployment.spec.template.spec.containers[0].volume_mounts = [mount_volume]
#
# # define deployment volume, be aware on windows add /run/desktop/mnt/host/c/ befor path
# volume = V1Volume(
#     name=volume_name,
#     host_path=V1HostPathVolumeSource(path="/run/desktop/mnt/host/c/Users/therm/Documents/Arbeit/HSMannheim/09-Projekte/FlowmIT")
# )
# deployment.spec.template.spec.volumes = [volume]
#
# #update deployment
# resp = api_instance.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
# print(resp)
