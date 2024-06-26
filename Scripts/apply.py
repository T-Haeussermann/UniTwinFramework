import os


# import registry authentification secret
os.system("kubectl create namespace dt")
os.system('kubectl get secret registry-auth -n docker-registry -o yaml | sed s/"namespace: docker-registry"/"namespace: dt"/ | kubectl apply -n dt -f -')

os.system("kubectl apply -f ./../Kubernetes --recursive=true")



