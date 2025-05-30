
# UniTwin
Framework for providing universal containerized Digital Twins with modular structure in Kubernetes.\
This Fraemwork was published in the following Papers. If you find it useful for your research, please consider citing it.

| DOI | Title | Stage          | Cite                   |
| --- | ----- |----------------|------------------------|
|[**10.1109/ICECCME57830.2023.10253365**](https://doi.org/10.1109/ICECCME57830.2023.10253365) | **Conceptual Architecture for the Provision and Aggregation of Universal Digital Twins within Containerization Environments** | Concept | [`Hae2023`](#Citation) |
|[**10.1109/MIC.2024.3489876**](https://doi.org/10.1109/MIC.2024.3489876) | **UniTwin: Pushing Universal Digital Twins Into the Clouds Through Reconfigurable Container Environments** | Implementation | [`Hae2025`](#Citation) |

## Citation

If you use UniTwin in your research, please consider citing the following publications:

```bibtex
@INPROCEEDINGS{Hae2023,
  title     = {Conceptual Architecture for the Provision and Aggregation of Universal Digital Twins within Containerization Environments},
  url       = {http://dx.doi.org/10.1109/ICECCME57830.2023.10253365},
  DOI       = {10.1109/iceccme57830.2023.10253365},
  booktitle = {2023 3rd International Conference on Electrical, Computer, Communications and Mechatronics Engineering (ICECCME)},
  publisher = {IEEE},
  author    = {Häußermann, Tim and Lehmann, Joel and Rache, Alessa and Reichwald, Julian},
  year      = {2023},
  month     = jul,
  pages     = {1--6}
}
}
```
```bibtex
@article{Hae2025,
  title     = {UniTwin: Pushing Universal Digital Twins Into the Clouds Through Reconfigurable Container Environments},
  volume    = {29},
  number    = {1},
  pages     = {8--15},
  ISSN      = {1941-0131},
  url       = {http://dx.doi.org/10.1109/MIC.2024.3489876},
  DOI       = {10.1109/mic.2024.3489876},
  journal   = {IEEE Internet Computing},
  publisher = {Institute of Electrical and Electronics Engineers (IEEE)},
  author    = {Häußermann, Tim M. and Lehmann, Joel and Rache, Alessa and Kolb, Florian and Wühler, Felix and Reichwald, Julian},
  year      = {2025},
  month     = jan
}
```

## Architecture
<img src="img/Concept.svg" width="100%" />

From: [**10.1109/ICECCME57830.2023.10253365**](https://doi.org/10.1109/ICECCME57830.2023.10253365)

## Implementation
<img src="img/Implementation.svg" width="100%" />

From: [**10.1109/MIC.2024.3489876**](https://doi.org/10.1109/MIC.2024.3489876)

## Prequisits
1. Running Kubernetes-Cluster
2. Private Docker Registry in the cluster
3. Kubernetes Secret for Registry in namespace docker-registry\
\
If you need help setting up th Kubernetes-Custer and Registry have a look at:\
[Kubernetes-Cluster-Setup](https://github.com/HyperSpec-FDM/Kubernetes-Cluster-Setup)


## Installation
1. Build images: UniTwin and DTPS
- Modify [buildUmages.py](Scripts/buildImages.py)
- Change Private Docker Registry Endpoint, User and Password
- Set dtps, unitwin and chatmodelprovider to True
- Set pushonly to False
- Change Private Docker Registry Endpoint in [class_kube_twin.py](DTPS/Functions/class_kube_twin.py)
- Run the script to Build the images and push them to your Private Docker Registry
run [buildUmages.py](Scripts/buildImages.py)
````
python3 Scripts/buildImages.py
````


2. Deploy to your Kubernetes-Clusters
- Modify yaml files in [Kubernetes](Kubernetes): change Private Docker Registry Endpoint in [01-dtps-k8.yaml](Kubernetes/05-dtps/01-dtps-k8.yaml) and [01-dtps-k8.yaml](Kubernetes/06-chat-model-provider/01-chat-model-provider-k8.yaml))
run [buildUmages.py](Scripts/buildImages.py)
````
python3 Scripts/apply.py
````

## Usage
1. Create the configuration for your required Digital Twin
- Use the JSON Builder for convenience. It is serverd under: [http://0.0.0.0:32000/dtps/](http://0.0.0.0:32000/dtps/)
- add and remove classes for needed functionalities in the class section
- customize class instances in the JSON Output section
- Publish Subscribe mechanism can be added to the classes.\
  _subscribers: adds subscribers to class instance.\
  Key = name of subscriber class instance, value = subscriber class instances subscription method
- _subscriptions: subscribes class instance to other class instance\
  Key = name of publisher class instance, value = subscriber class instances subscription method
2. Deploy the Digital Twin to the Cluster\
a) Use DTPS Swagger UI under [DTPS](http://0.0.0.0:32000/dtps/docs#)\
   Use method createTwin\
b) curl -X 'POST' \
  'http://0.0.0.0:32000/dtps/createTwin?conf={YourConfig}&version=1.0&assignNode=false' \
  -H 'accept: application/json' \
  -d ''
3. Interact with your Digital Twins API Endpoints under: [http://0.0.0.0:32000/{DigitalTwinsUID}/docs#](http://0.0.0.0/{DigitalTwinsUID}/docs#)
4. Use the chat interface under [http://0.0.0.0:32000/{DigitalTwinsUID}/](http://0.0.0.0/{DigitalTwinsUID}/chat) to get attributes and run commands
- examples: What is your uid? What are your children? Use child class_MQTT-I1 and run method publish with parameters Topic=Test, Payload=Test

## Customization
1. Create your own class for your need and place it in [DTPS/Modules](DTPS/Modules)
- Name of the file must match the classes name and contain the following imports and structure:
````
from .class_ComponentABC import Component
from .class_Event import Event

class class_MQTT(Component):
````
2. Define base configuration to use in JSON Builder
- Filename should be class_yourName.json
3. Rebuild and Redeploy DTPS
