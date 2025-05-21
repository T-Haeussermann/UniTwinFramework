import os

# Define UniTwin_standalone Dockerfile, Version and Tag
dockerfileUniTwin = "./DockerfileUniTwinStandalone"
versionUniTwin = "1.0"
tagUniTwin = "unitwin_standalone:" + versionUniTwin

# Define additional variables
docker_ignore_file = ".dockerignore"
module_path = "DTPS/Modules"
add_classes = ["class_MQTT", "method_MQTT"]

# Change working directory
os.chdir("..")

def buildImage(dockerfile, tag):
    buildCommand = f"docker build --no-cache -t {tag} -f {dockerfile} ."
    os.system(buildCommand)

# Clean up system to prevent full storage
cleancommand = "docker system prune -f"
os.system(cleancommand)

# clear dockerignore file
with open(docker_ignore_file, "w") as file:
    file.write("# .dockerignore\n")

# add files to dockerignore
all_classes = [path.replace(".py", "") for path in os.listdir(module_path)]
dockerignore_list = list(set(all_classes) - set(add_classes))
with open(docker_ignore_file, "a") as file:
    for item in dockerignore_list:
        file.write("%s\n" % f"{module_path}/{item}.py")


# Build the desired image or images and push to local registry
buildImage(dockerfileUniTwin, tagUniTwin)

# remove .dockerignore
os.remove(".dockerignore")



