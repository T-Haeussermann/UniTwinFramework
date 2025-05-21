import os
from kubernetes import client, config

def get_pod_name_by_deployment(deployment_name, namespace, container_name):
    # Load the Kubernetes configuration
    config.load_kube_config()

    # Create an instance of the Kubernetes AppsV1 API client
    apps_v1 = client.AppsV1Api()

    # Get the deployment object
    deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)

    # Get the labels selector for the deployment's pod template
    labels = deployment.spec.selector.match_labels

    # Create an instance of the Kubernetes CoreV1 API client
    core_v1 = client.CoreV1Api()

    # List pods in the same namespace with matching labels
    pods = core_v1.list_namespaced_pod(namespace, label_selector=','.join(f"{k}={v}" for k, v in labels.items())).items

    # Return the name of the first pod (assuming there is only one)
    if pods:
        for pod in pods:
            print(f"Containers in pod '{pod.metadata.name}':")
            for container_status in pod.status.container_statuses:
                name = container_status.name
                container_id = container_status.container_id
                if name == container_name:
                    cid = container_id.replace("docker://", "")
        return pods[0].metadata.name, cid
    else:
        return None


paths = ["DTPS/Modules", "DTPS/json_configurator/templates/jsonFiles", "DTPS/Descriptions"]
deployment_name = "dtps"
namespace = "dt"
container_name = "dtps"

dtps_pod_name, dtps_pod_id = get_pod_name_by_deployment(deployment_name, namespace, container_name)

os.chdir("..")
for path in paths:
    for file in os.listdir(path):
        if os.path.isfile(f"{path}/{file}"):
            command = f"kubectl cp {path}/{file} {namespace}/{dtps_pod_name}:/{path}/{file} -c {container_name}"
        elif os.path.isdir(f"{path}/{file}"):
            command = f"kubectl cp {path}/{file} {namespace}/{dtps_pod_name}:/{path} -c {container_name}"
        os.system(command)

