import time
import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

local_deployment = True

# import registry authentification secret
os.system("kubectl create namespace dt")
os.system('kubectl get secret registry-auth -n docker-registry -o yaml | sed s/"namespace: docker-registry"/"namespace: dt"/ | kubectl apply -n dt -f -')

os.system("kubectl apply -f ./../Kubernetes --recursive=true")

if local_deployment:
    # Load kubeconfig
    config.load_kube_config()

    # Define PVCs and namespace
    namespace = "dt"
    pvcs = ["cs-data", "dt-db-data", "chatmodelprovider-pvc"]
    new_storage_class = "hostpath"  # change to your desired StorageClass

    # Create Kubernetes API client
    v1 = client.CoreV1Api()


    def wait_for_pvc_deletion(name, namespace, timeout=60):
        for _ in range(timeout):
            try:
                v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
                print(f"Waiting for PVC {name} to be fully deleted...")
                time.sleep(2)
            except ApiException as e:
                if e.status == 404:
                    print(f"PVC {name} is fully deleted.")
                    return True
                else:
                    raise
        print(f"Timeout waiting for PVC {name} deletion.")
        return False


    for pvc_name in pvcs:
        try:
            pvc = v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
            pvc_spec = pvc.spec

            print(f"Deleting PVC: {pvc_name}")
            v1.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)

            if wait_for_pvc_deletion(pvc_name, namespace):
                pvc_spec.storage_class_name = new_storage_class
                new_pvc = client.V1PersistentVolumeClaim(
                    metadata=client.V1ObjectMeta(name=pvc_name),
                    spec=pvc_spec
                )
                print(f"Recreating PVC: {pvc_name} with storageClass: {new_storage_class}")
                v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=new_pvc)
            else:
                print(f"Skipping recreation of PVC: {pvc_name} due to timeout.")
        except ApiException as e:
            print(f"Error with PVC {pvc_name}: {e}")

