from kubernetes import client, config
def listTwins(namespace):

    # in cluster
    #config.load_kube_config()
    config.load_incluster_config()

    # Define the Kubernetes API client
    api_client = client.ApiClient()

    # Get List of deployment
    api_instance = client.AppsV1Api(api_client)
    deployment_list = []
    for item in api_instance.list_namespaced_deployment(namespace=namespace).items:
        deployment_list.append(item.metadata.name)

    return deployment_list