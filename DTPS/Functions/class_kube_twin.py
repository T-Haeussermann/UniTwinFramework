from kubernetes import client, config
from kubernetes.client.models import (
    V1Deployment,
    V1DeploymentSpec,
    V1LabelSelector, V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1Container,
    V1ContainerPort,
    V1Service,
    V1ServicePort,
    V1ServiceSpec,
    V1Ingress,
    V1HTTPIngressPath,
    V1HTTPIngressRuleValue,
    V1IngressRule,
    V1IngressSpec,
    V1IngressServiceBackend,
    V1ServiceBackendPort,
    V1IngressBackend,
    V1EnvVar,
    V1Volume,
    V1PersistentVolume,
    V1PersistentVolumeClaim,
    V1HostPathVolumeSource,
    V1LocalObjectReference,
    V1VolumeMount)
import os
import json

class kube_twin():

    def __init__(self, namespace):
        # in cluster
        # config.load_kube_config()
        config.load_incluster_config()

        # Define the Kubernetes API client
        self.api_client = client.ApiClient()
        self.namespace = namespace

        # Define registry to use
        self.registry = "registry_ip:registry_port"

        # Define memory path for serializing deployments
        self.memory_path = "memory/deployments.json"

    def defineTwin(self, uid, version):

        # Define the namespace for the deployment, service, and ingress
        namespace = "dt"

        # Define the name for the deployment, service, ingress, persistent volume and persistent volume claim
        name = "dt-" + uid
        name_svc = name + "-svc"
        name_ingress = name + "-ingress"
        name_pv = name + "-pv"
        name_pvc = name + "-pvc"

        # Define the container image and port
        container_image = self.registry + "/" + "unitwin:" + str(version)
        container_port = 7000

        # Define return dict
        return_dict = {"uid": uid,
                       "namespace": namespace,
                       "name": name,
                       "name_svc": name_svc,
                       "name_ingress": name_ingress,
                       "name_pv": name_pv,
                       "name_pvc": name_pvc,
                       "container_image": container_image,
                       "container_port": container_port}

        if version == None:
            return_dict.pop("container_image")
            return_dict.pop("container_port")
        print(return_dict)
        return return_dict

    def deployTwin(self, definition, assignNode=False, node_name=None):

        # define uid
        uid = definition["uid"]

        # Define the namespace for the deployment, service, and ingress
        namespace = definition["namespace"]

        # Define the name for the deployment
        name = definition["name"]
        name_svc = definition["name_svc"]
        name_ingress = definition["name_ingress"]

        # Define the container image and port
        container_image = definition["container_image"]
        container_port = definition["container_port"]

        response_deployment = self.createDeployment(uid, namespace, name, container_image, container_port, assignNode, node_name)
        response_service = self.createService(namespace, name, name_svc, container_port)
        response_ingress = self.createIngress(namespace, name, name_svc, name_ingress)
        resp = {"deployment": response_deployment, "service": response_service, "ingress": response_ingress}

        return resp

    def createDeployment(self, uid, namespace, name, container_image, container_port, assignNode, node_name):

        # Define the deployment spec
        deployment_spec = V1DeploymentSpec(
            replicas=1,
            selector=V1LabelSelector(match_labels={"app": name}),
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels={"app": name}),
                spec=V1PodSpec(
                    containers=[V1Container(
                        name=name,
                        image=container_image,
                        image_pull_policy="IfNotPresent",
                        ports=[V1ContainerPort(container_port=container_port)],
                        env=[
                            V1EnvVar(name="uid", value=uid),
                            V1EnvVar(name="DISPLAY", value=os.getenv("DISPLAY"))
                        ]
                    )],
                    image_pull_secrets=[V1LocalObjectReference(name="registry-auth")]
                )
            )
        )

        # Define the deployment object
        deployment = V1Deployment(
            metadata=V1ObjectMeta(name=name),
            spec=deployment_spec,
        )

        # Assign Node if selected
        if assignNode is True:
            print("assigning node:", node_name)
            # Define node affinity to target the desired node
            node_affinity = client.V1Affinity(
                node_affinity=client.V1NodeAffinity(
                    required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                        node_selector_terms=[
                            client.V1NodeSelectorTerm(
                                match_expressions=[
                                    client.V1NodeSelectorRequirement(
                                        key="kubernetes.io/hostname",
                                        operator="In",
                                        values=[node_name]
                                    )
                                ]
                            )
                        ]
                    )
                )
            )

            # Update the affinity in the pod template specification
            deployment.spec.template.spec.affinity = node_affinity

        # Create the deployment
        api_instance = client.AppsV1Api(self.api_client)
        response_deployment = api_instance.create_namespaced_deployment(body=deployment, namespace=namespace).status
        print("Deployment created. status='%s'" % str(response_deployment))
        # self.serializeDeployment(uid, deployment)
        return response_deployment

    def createService(self, namespace, name, name_svc, container_port):

        # Define the service object
        service = V1Service(
            metadata=V1ObjectMeta(name=name_svc),
            spec=V1ServiceSpec(
                selector={"app": name},
                ports=[V1ServicePort(port=container_port)],
                type="ClusterIP",
            ),
        )

        # Create the service
        api_instance = client.CoreV1Api(self.api_client)
        response_service = api_instance.create_namespaced_service(body=service, namespace=namespace).status
        print("Service created. status='%s'" % str(response_service))
        return response_service

    def createIngress(self, namespace, name, name_svc, name_ingress):

        # Create the ingress
        ingress = V1Ingress(
            metadata=V1ObjectMeta(name=name_ingress,
                                  annotations={"kubernetes.io/ingress.class": "nginx",
                                               "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
                                               "nginx.ingress.kubernetes.io/use-regex": "true",
                                               "nginx.ingress.kubernetes.io/enable-rewrite-log": "true"}),
            spec=V1IngressSpec(
                rules=[
                    V1IngressRule(
                        # host="localhost",
                        http=V1HTTPIngressRuleValue(
                            paths=[
                                V1HTTPIngressPath(
                                    path="/" + name + "(/|$)(.*)",
                                    path_type="Prefix",
                                    backend=V1IngressBackend(
                                        service=V1IngressServiceBackend(
                                            port=V1ServiceBackendPort(
                                                number=7000,
                                            ),
                                            name=name_svc)
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )

        api_instance = client.NetworkingV1Api(self.api_client)
        response_ingress = api_instance.create_namespaced_ingress(namespace=namespace, body=ingress).status
        print("Ingress created. status='%s'" % str(response_ingress))
        return response_ingress
    def deleteTwin(self, definition):

        # Define the namespace for the deployment, service, and ingress
        namespace = definition["namespace"]

        # Define the name for the deployment
        name = definition["name"]
        name_svc = definition["name_svc"]
        name_ingress = definition["name_ingress"]

        # Define response
        resp = {}

        # Delete the deployment
        api_instance = client.AppsV1Api(self.api_client)
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
        api_instance = client.CoreV1Api(self.api_client)
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
        api_instance = client.NetworkingV1Api(self.api_client)
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

    def loadTwin(self, definition, assignNode=False, node_name=None):

        # define uid
        uid = definition["uid"]

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
        api_instance = client.AppsV1Api(self.api_client)
        deployment_list = []
        for item in api_instance.list_namespaced_deployment(namespace=namespace).items:
            deployment_list.append(item.metadata.name)

        if name not in deployment_list:
            print(name + " not in deployment list. Creating deployment")
            resp["deployment"] = self.createDeployment(uid, namespace, name, container_image, container_port, assignNode, node_name)
        else:
            print(name + " is in deployment list. Doing nothing.")
            resp["deployment"] = "already running"

        # Get List of service
        api_instance = client.CoreV1Api(self.api_client)
        service_list = []
        for item in api_instance.list_namespaced_service(namespace=namespace).items:
            service_list.append(item.metadata.name)

        if name_svc not in service_list:
            print(name_svc + " not in service list. Creating service.")
            resp["service"] = self.createService(namespace, name, name_svc, container_port)
        else:
            print(name_svc + " is in service list. Doing nothing.")
            resp["service"] = "already running"

        # Get List of ingress
        api_instance = client.NetworkingV1Api(self.api_client)
        ingress_list = []
        for item in api_instance.list_namespaced_ingress(namespace=namespace).items:
            ingress_list.append(item.metadata.name)

        if name_ingress not in ingress_list:
            print(name_ingress + " not in ingress list. Creating ingress.")
            resp["ingress"] = self.createIngress(namespace, name, name_svc, name_ingress)
        else:
            print(name_ingress + " is in ingress list. Doing nothing.")
            resp["ingress"] = "already running"

        return resp

    def listTwins(self, namespace):

        # in cluster
        # config.load_kube_config()
        config.load_incluster_config()

        # Get List of deployment
        api_instance = client.AppsV1Api(self.api_client)
        deployment_list = []
        for item in api_instance.list_namespaced_deployment(namespace=namespace).items:
            deployment_list.append(item.metadata.name)

        return deployment_list

    def mountTwin(self, definition, path):
        # Get Nodes
        nodes = self.listNodes()
        if type(nodes) == list:
            nodes = len(nodes)
            if nodes == 1:
                print("Single Node Cluster")
                self.mountTwinSingleNode(definition, path)

            elif nodes > 1:
                print("Multi Node Cluster")
                self.mountTwinMultiNode(definition, path)

            else:
                return "Error"
        else:
            print("Error getting Nodes!")

    def mountTwinSingleNode(self, definition, path):

        # Define the Kubernetes API instance
        api_instance = client.AppsV1Api(self.api_client)

        # Define the namespace for the deployment, service, and ingress
        namespace = definition["namespace"]

        # Define the name for the deployment
        name = definition["name"]
        volume_name = name

        # Define path for Windows machines
        if "\\" in path:
            path = path.replace("C:\\", "")
            path = "/run/desktop/mnt/host/c/" + path.replace("\\", "/")

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
            print(deployment)
            resp = api_instance.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
            print(resp)

        else:
            resp = "Already mounted"

        return {definition["uid"]: resp}

    def mountTwinMultiNode(self, definition, path):

        # Define the Kubernetes API instance
        api_instance = client.AppsV1Api(self.api_client)

        # Define the namespace for the deployment, service, and ingress
        namespace = definition["namespace"]

        # Define the name for the deployment and volume
        name = definition["name"]
        volume_name = name

        # Define the name for persistent volume
        name_pv = definition["name_pv"]

        # Define the name for persistent volume
        name_pvc = definition["name_pvc"]

        # # Get current
        # currentNode = self.listCurrentNode(name, namespace)
        # print(currentNode)
        #
        # # Create Persistent Volume
        # self.createPersistentVolume(name_pv, path, currentNode)
        #
        # # Create Persistent Volume Claim
        # self.createPersistentVolumeClaim(name_pvc)

        # Define path for Windows machines
        if "\\" in path:
            path = path.replace("C:\\", "")
            path = "/run/desktop/mnt/host/c/" + path.replace("\\", "/")

        # get deployment
        deployment = api_instance.read_namespaced_deployment(name=name, namespace=namespace)
        print(deployment)

        if deployment.spec.template.spec.containers[0].volume_mounts == None:
            # Define the volume mount
            mount_volume = V1VolumeMount(mount_path="UniTwin/watch", name=volume_name)
            deployment.spec.template.spec.containers[0].volume_mounts = [mount_volume]

            # Define the X11-unix mount
            mount_X11 = V1VolumeMount(mount_path="/tmp/.X11-unix", name="xserver")
            deployment.spec.template.spec.containers[0].volume_mounts.append(mount_X11)
            # mount_Xauth = V1VolumeMount(mount_path="$HOME/.Xauthority", name="xauth")
            # deployment.spec.template.spec.containers[0].volume_mounts.append(mount_X11)

            # Define deployment volume, be aware on windows add /run/desktop/mnt/host/c/ befor path
            volume = V1Volume(
                name=volume_name,
                host_path=V1HostPathVolumeSource(
                    path=path)
            )
            deployment.spec.template.spec.volumes = [volume]

            # Define X11-unix volume
            X11_volume = V1Volume(
                name="xserver",
                host_path=V1HostPathVolumeSource(
                    path="/tmp/.X11-unix")
            )
            deployment.spec.template.spec.volumes.append(X11_volume)

            # Update deployment
            print(deployment)
            resp = api_instance.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
            print(resp)

        else:
            resp = "Already mounted"

        return {definition["uid"]: resp}

    def get_pod_name_by_deployment(self, deployment_name, namespace):

        # Create an instance of the Kubernetes AppsV1 API client
        apps_v1 = client.AppsV1Api(self.api_client)

        # Get the deployment object
        try:
            deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        except:
            deployment = None

        # Get the labels selector for the deployment's pod template
        if deployment:
            labels = deployment.spec.selector.match_labels

            # Create an instance of the Kubernetes CoreV1 API client
            core_v1 = client.CoreV1Api(self.api_client)

            # List pods in the same namespace with matching labels
            pods = core_v1.list_namespaced_pod(namespace,
                                               label_selector=','.join(f"{k}={v}" for k, v in labels.items())).items

            # Return the name of the first pod (assuming there is only one)
            if pods:
                for pod in pods:
                    print(f"Containers in pod '{pod.metadata.name}':")
                    for container_status in pod.status.container_statuses:
                        name = container_status.name
                        container_id = container_status.container_id
                return pods[0].metadata.name
            else:
                return None

        else:
            return None

    def listNodes(self):

        # Create an instance of the Kubernetes CoreV1 API client
        api_instance = client.CoreV1Api(self.api_client)
        try:
            nodes = api_instance.list_node().items

            # Extract node names from the list of dictionaries
            node_names = [node.metadata.name for node in nodes]

            return node_names
        except Exception as e:
            return {"error": str(e)}

    def listCurrentNode(self, deployment_name, namespace):

        # Create an instance of the Kubernetes CoreV1 API client
        core_v1 = client.CoreV1Api(self.api_client)

        # Get Pod by deployment name
        pod_name = self.get_pod_name_by_deployment(deployment_name, namespace)

        if pod_name:
            # Fetch the Pod object
            pod = core_v1.read_namespaced_pod(pod_name, namespace)

            # Extract the node name from the Pod object
            node_name = pod.spec.node_name
            return {deployment_name: node_name}
        else:
            return None

    def assignNode(self, deployment_name, namespace, node_name):

        # Create an instance of AppsV1
        api_instance = client.AppsV1Api(self.api_client)

        # Get the existing deployment
        deployment = api_instance.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Check if the pods are already assigned to the desired node
        if deployment.spec.template.spec.affinity and deployment.spec.template.spec.affinity.node_affinity:
            existing_node_affinity = deployment.spec.template.spec.affinity.node_affinity
            for term in existing_node_affinity.required_during_scheduling_ignored_during_execution.node_selector_terms:
                for req in term.match_expressions:
                    if req.key == "kubernetes.io/hostname" and req.values == [node_name]:
                        return f"Deployment {deployment_name} is already assigned to node {node_name}"

        # Define node affinity to target the desired node
        node_affinity = client.V1Affinity(
            node_affinity=client.V1NodeAffinity(
                required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                    node_selector_terms=[
                        client.V1NodeSelectorTerm(
                            match_expressions=[
                                client.V1NodeSelectorRequirement(
                                    key="kubernetes.io/hostname",
                                    operator="In",
                                    values=[node_name]
                                )
                            ]
                        )
                    ]
                )
            )
        )

        # Update the affinity in the pod template specification
        deployment.spec.template.spec.affinity = node_affinity

        # Update the deployment
        updated_deployment = api_instance.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )

        return f"Deployment {deployment_name} updated to assign pods to node {node_name}"

    def serializeDeployment(self, uid, deployment):

        if os.path.isfile(self.memory_path) == True:
            with open(self.memory_path, "r") as file:
                deploymentFile = json.load(file)
        else:
            deploymentFile = {}

        deploymentFile[uid] = deployment

        with open(self.memory_path, "w") as file:
            json.dump(deploymentFile, file, indent=4)

