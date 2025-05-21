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
    V1HostPathVolumeSource,
    V1VolumeMount)
import os


def deployTwin(definition):
    # define uid
    uid = definition["uid"]

    # config.load_incluster_config()
    # config.load_kube_config()

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

    response_deployment = createDeployment(uid, api_client, namespace, name, container_image, container_port)
    response_service = createService(api_client, namespace, name, name_svc, container_port)
    response_ingress = createIngress(api_client, namespace, name, name_svc, name_ingress)
    resp = {"deployment": response_deployment, "service": response_service, "ingress": response_ingress}
    print(resp)
    return resp


def createDeployment(uid, api_client, namespace, name, container_image, container_port):
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
                image_pull_secrets=[{"name": "registry-auth"}]
            )
        )
    )

    # Define the deployment object
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name=name),
        spec=deployment_spec,
    )

    # Create the deployment
    api_instance = client.AppsV1Api(api_client)
    response_deployment = api_instance.create_namespaced_deployment(body=deployment, namespace=namespace).status
    print("Deployment created. status='%s'" % str(response_deployment))
    return response_deployment


def createService(api_client, namespace, name, name_svc, container_port):
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
    api_instance = client.CoreV1Api(api_client)
    response_service = api_instance.create_namespaced_service(body=service, namespace=namespace).status
    print("Service created. status='%s'" % str(response_service))
    return response_service


def createIngress(api_client, namespace, name, name_svc, name_ingress):
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
                    host="localhost",
                    http=V1HTTPIngressRuleValue(
                        paths=[
                            V1HTTPIngressPath(
                                path="/" + name + "(/|$)(.*)",
                                path_type="ImplementationSpecific",
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

    api_instance = client.NetworkingV1Api(api_client)
    response_ingress = api_instance.create_namespaced_ingress(namespace=namespace, body=ingress).status
    print("Ingress created. status='%s'" % str(response_ingress))
    return response_ingress
