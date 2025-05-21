from kubernetes import client, config
from .deployTwin import createDeployment, createService, createIngress

def existTwin(definition):

    # define uid
    uid = definition["uid"]

    # config.load_incluster_config()
    #config.load_kube_config()

    # Define the Kubernetes API client
    api_client = definition["api_client"]

    # Define the namespace for the deployment, service, and ingress
    namespace = definition["namespace"]

    # Define the name for the deployment
    name = definition["name"]
    name_svc = definition["name_svc"]
    name_ingress = definition["name_ingress"]

    # Define the container image and port
    container_image = definition["container_image"]
    container_port = definition["container_port"]

    # Define response
    resp = {}

    # Get List of deployment
    api_instance = client.AppsV1Api(api_client)
    deployment_list = []
    for item in api_instance.list_namespaced_deployment(namespace=namespace).items:
        deployment_list.append(item.metadata.name)

    if name not in deployment_list:
        print(name + " not in deployment list. Creating deployment")
        resp["deployment"] = createDeployment(uid, api_client, namespace, name, container_image, container_port)
    else:
        print(name + " is in deployment list. Doing nothing.")
        resp["deployment"] = "already running"


    # Get List of service
    api_instance = client.CoreV1Api(api_client)
    service_list = []
    for item in api_instance.list_namespaced_service(namespace=namespace).items:
        service_list.append(item.metadata.name)

    if name_svc not in service_list:
        print(name_svc + " not in service list. Creating service.")
        resp["service"] = createService(api_client, namespace, name, name_svc, container_port)
    else:
        print(name_svc + " is in service list. Doing nothing.")
        resp["service"] = "already running"

    # Get List of ingress
    api_instance = client.NetworkingV1Api(api_client)
    ingress_list = []
    for item in api_instance.list_namespaced_ingress(namespace=namespace).items:
        ingress_list.append(item.metadata.name)

    if name_ingress not in ingress_list:
        print(name_ingress + " not in ingress list. Creating ingress.")
        resp["ingress"] = createIngress(api_client, namespace, name, name_svc, name_ingress)
    else:
        print(name_ingress + " is in ingress list. Doing nothing.")
        resp["ingress"] = "already running"

    return resp




