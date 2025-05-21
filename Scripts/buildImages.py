import os

# Define DTPS Dockerfile, Version and Tag
dockerfileDTPS = "./DockerfileDTPS"
versionDTPS = "1.0"
tagDTPS = "dtps:" + versionDTPS

# Define UniTwin Dockerfile, Version and Tag
dockerfileUniTwin = "./DockerfileUniTwin"
versionUniTwin = "1.0"
tagUniTwin = "unitwin:" + versionUniTwin

# Define Chat-Modell-Provider Dockerfile, Version and Tag
dockerfileChatModelProvider = "./DockerfileChatModelProvider"
versionChatModelProvider = "1.0"
tagChatModelProvider = "chatmodelprovider:" + versionChatModelProvider

# Define privat registry endpoint
registry = "192.168.100.11:31000"
user = "tim"
password = "changeme"

# Define which image to build and push
dtps = False
unitwin = True
chatmodelprovider = False
buildonly = True
pushonly = False

# Change working directory
os.chdir("..")


def buildImage(dockerfile, tag):
    buildCommand = f"docker build --no-cache -t {tag} -f {dockerfile} ."
    os.system(buildCommand)

def pushToRegistry(imageTag, registry):
    if not buildonly:
        loginCommand = f"docker login -u {user} -p {password} 192.168.100.11:31000"
        os.system(loginCommand)

    tagCommand = f"docker tag {imageTag} {registry}/{imageTag}"
    os.system(tagCommand)

    if not buildonly:
        pushCommand = f"docker push {registry}/{imageTag}"
        print(pushCommand)
        os.system(pushCommand)

# Clean up system to prevent full storage
cleancommand = "docker system prune -f"
os.system(cleancommand)

# Build the desired image or images and push to local registry
if dtps:
    if not pushonly:
        buildImage(dockerfileDTPS, tagDTPS)
    pushToRegistry(tagDTPS, registry)
if unitwin:
    if not pushonly:
        buildImage(dockerfileUniTwin, tagUniTwin)
    pushToRegistry(tagUniTwin, registry)
if chatmodelprovider:
    if not pushonly:
        buildImage(dockerfileChatModelProvider, tagChatModelProvider)
    pushToRegistry(tagChatModelProvider, registry)


