# run docker containers and maintain 190 containers running at a time
#
import subprocess
import time
import threading
import sys
import requests
import json
import base64
import os
import docker

# afdfadf setting up the environment
if "PROD" in os.environ:
    baseUrl = "https://fhdsxjdwjuo4chghz7mlaw2cju0ppwfx.lambda-url.us-east-1.on.aws/"
    bucket = "gersteincodegenprod"
    ecr_repo = "passatkrunner"
elif "TESTING" in os.environ:
    baseUrl="https://wnn2rjzzw2nkqj6yfbbp5igfmy0yxemy.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegentest"
    ecr_repo = "passatkrunnertest"
else:
    raise Exception("No environment variable set")

s3Url = "http://" +bucket + ".s3-website-us-east-1.amazonaws.com"

docker_base_url = "public.ecr.aws/i5g0m1f6"
client = docker.from_env()

def get_data():
    global baseUrl
    # check if DATA_BASE64 is set
    if "DATA_BASE64" in os.environ:
        # decode the data
        data = base64.b64decode(os.environ["DATA_BASE64"])
        # load the data
        json_data = json.loads(data)
        return json_data

    if "MANUAL_TEST_CASE" in os.environ:
        # manual test case is a filepath to a json file
        with open(os.environ["MANUAL_TEST_CASE"], "r") as f:
            json_data = json.load(f)
        return json_data
    response = requests.get(baseUrl + "/get")
    if response.status_code == 200:
        if (response.text == ""): return None
        json_res = json.loads(response.text)
        return json_res
    else:
        return None

# def run_docker(detach=True):
#     data = get_data()
#     if data is None:
#         print("No data received, exiting")
#         return None
#     data_base64 = base64.b64encode(json.dumps(data).encode("utf-8"))
#     repo_name = data["test_case_repo"].replace("/", "_")
#     environ_data_command = "DATA_BASE64=" + data_base64.decode("utf-8")
#     docker_image_name = docker_base_url + "/" + ecr_repo+":"+repo_name
#     environ_type_command = "TESTING=true" if "TESTING" in os.environ else "PROD=true"
#     command_sequence = ["docker", "run", "-d", "-e", environ_type_command, "--network=host", "-it", "--cpus=1", "-e", environ_data_command, docker_image_name]
#     # remove -d if detach is false
#     if not detach:
#         command_sequence.remove("-d")
#     subprocess.run(command_sequence)
#     # subprocess.run(["docker", "run", "-d", "--network=host", "-it", '--cpus=1', "passatkrunner"])


# ====================== VERSION 2 ======================
# def run_docker(detach=True):
#     repo_name = "lilbillybiscuit_323tester"
#     docker_image_name = docker_base_url + "/" + ecr_repo+":"+repo_name
#     environ_type_command = "TESTING=true" if "TESTING" in os.environ else "PROD=true"
#     command_sequence = ["docker", "run", "-d", "-e", environ_type_command, "--network=host", "-it", "--cpus=1",  docker_image_name]
#     # remove -d if detach is false
#     if not detach:
#         command_sequence.remove("-d")
#     print(command_sequence)
#     subprocess.run(command_sequence)

# ====================== VERSION 3 ======================

def run_docker(detach=True):
    repo_name = "lilbillybiscuit_323tester"
    docker_image_name = docker_base_url + "/" + ecr_repo + ":" + repo_name
    environ_type = "TESTING" if "TESTING" in os.environ else "PROD"
    environment = {environ_type: "true"}

    container = client.containers.run(
        image=docker_image_name,
        detach=True,
        environment=environment,
        network_mode="host",
        tty=True,
        cpu_count=1,
    )

    if not detach:
        logs = container.logs(stream=True)
        for log in logs:
            print(log.decode("utf-8"), end="")
        container.remove(force=True)


# def get_docker_count():
#     # return the number of docker containers running with the ecr_repo image
#     output = subprocess.run(["docker", "ps", "--filter", "ancestor="+ecr_repo, "--format", "{{.ID}}"], stdout=subprocess.PIPE)
#     return len(output.stdout.decode("utf-8").split("\n")) - 1

def get_docker_count():
    containers = client.containers.list()
    return len(containers)


def launch_docker_in_loop():
    global numcontainers
    while True:
        ct = get_docker_count()
        print("Count: " + str(ct))
        if ct < numcontainers:
            for i in range((numcontainers - ct)//8-1):
                run_docker()
            run_docker()
        else:
            pass
        time.sleep(1)

def delete_stopped_containers(interval= 60):
    while True:
        # run prune every 60 seconds
        client.containers.prune()
        
        # containers = client.containers.list(filters={'status': 'exited'})
        # print("Removing " + str(len(containers)) + " containers")
        # for container in containers:
        #     container.remove()
        time.sleep(interval)
  

print(get_docker_count())

if (len(sys.argv) < 2):
    print("Usage: python3 docker_runner.py <num_containers>")
    exit(1)
run_once=0
if len(sys.argv) == 3:
    
    try:
        run_once = int(sys.argv[2]) # should be 1
    except:
        run_once = 0

if run_once == 1:
    run_docker(detach=False)
    exit(0)

numcontainers = int(sys.argv[1])


image_name = "public.ecr.aws/i5g0m1f6/" + ecr_repo + ":base"
client.images.pull(image_name)
# subprocess.run(["docker", "tag", "public.ecr.aws/i5g0m1f6/passatkrunner:base", "passatkrunner"])

# launch docker containers in a loop with multiple threads
threads = []
for i in range(4):
    t = threading.Thread(target=launch_docker_in_loop)
    threads.append(t)
    t.start()

# start a thread to delete stopped containers
t = threading.Thread(target=delete_stopped_containers)
t.start()