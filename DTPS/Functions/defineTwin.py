from kubernetes import client, config
def defineTwin(uid, version):

    # in cluster
    # config.load_kube_config()
    config.load_incluster_config()

    # Define the Kubernetes API client
    api_client = client.ApiClient()

    # Define the namespace for the deployment, service, and ingress
    namespace = "dt"

    # Define the name for the deployment, service, ingress
    name = "dt-" + uid
    name_svc = name + "-svc"
    name_ingress = name + "-ingress"

    # Define the container image and port
    container_image = "192.168.100.11:31000/unitwin:" + str(version)
    container_port = 7000

    # Define return dict
    return_dict = {"uid": uid,
                   "api_client": api_client,
                   "namespace": namespace,
                   "name": name,
                   "name_svc": name_svc,
                   "name_ingress": name_ingress,
                   "container_image": container_image,
                   "container_port": container_port}

    if version == None:
        return_dict.pop("container_image")
        return_dict.pop("container_port")
    print(return_dict)
    return return_dict
