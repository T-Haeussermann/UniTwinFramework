import json
from kubernetes import client, config

def deleteTwin(definition):

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

    # Define response
    resp = {}

    # Delete the deployment
    api_instance = client.AppsV1Api(api_client)
    deployment_list = []
    for item in api_instance.list_namespaced_deployment(namespace=namespace).items:
        deployment_list.append(item.metadata.name)

    if name in deployment_list:
        response_deployment = api_instance.delete_namespaced_deployment(name=name, namespace=namespace).status
        print("Deployment deleted. status='%s'" % str(response_deployment))
        resp["deployment"] = response_deployment
    else:
        response_deployment = "No such deployment"
        print("No such deployment")
        resp["deployment"] = response_deployment

    # Delete the service
    api_instance = client.CoreV1Api(api_client)
    service_list = []
    for item in api_instance.list_namespaced_service(namespace=namespace).items:
        service_list.append(item.metadata.name)

    if name_svc in service_list:
        response_service = api_instance.delete_namespaced_service(name=name_svc, namespace=namespace).status
        print("Service deleted. status='%s'" % str(response_service))
        resp["service"] = response_service
    else:
        response_service = "No such service"
        print("No such service")
        resp["service"] = response_service

    # Delete the ingress
    api_instance = client.NetworkingV1Api(api_client)
    ingress_list = []
    for item in api_instance.list_namespaced_ingress(namespace=namespace).items:
        ingress_list.append(item.metadata.name)

    if name_ingress in ingress_list:
        response_ingress = api_instance.delete_namespaced_ingress(name=name_ingress, namespace=namespace).status
        print("Ingress deleted. status='%s'" % str(response_ingress))
        resp["ingress"] = response_ingress
    else:
        response_ingress = "No such ingress"
        print(response_ingress)
        resp["ingress"] = response_ingress

    return resp




