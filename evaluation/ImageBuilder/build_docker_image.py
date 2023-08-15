import subprocess
import time
import boto3
import json
import shlex
import sys
import os
import yaml

# afdfadf setting up the environment
if "TESTING" in os.environ:
    baseUrl = "https://fhdsxjdwjuo4chghz7mlaw2cju0ppwfx.lambda-url.us-east-1.on.aws/"
    bucket = "gersteincodegentest"
elif "PROD" in os.environ:
    baseUrl="https://wnn2rjzzw2nkqj6yfbbp5igfmy0yxemy.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegenprod"
else:
    raise Exception("No environment variable set")

s3Url = "http://" +bucket + ".s3-website-us-east-1.amazonaws.com"


with open("build_data.yaml", "r") as f:
    yaml_data = yaml.safe_load(f)

# TODO: Change these variables
repo_name= yaml_data["repo_name"]
pre_commands, build_commands, run_commands = [], [], []
global_environment = yaml_data["global_environment"] if "global_environment" in yaml_data else []

magic_string = "6SKLCZjnPzPdwztCY3wf5X1c9L1AsN2aHB4mWlmU"
def convert_command(command: str):
    global magic_string
    with open("/home/ubuntu/temp_command.sh", "w") as f:
        f.write("#!/bin/bash -l \n")
        f.write(command)
    command = "bash /home/ubuntu/temp_command.sh"
    command+="\necho $'\\n'; echo $'\\n'$?" + magic_string + "$'\\n'" + "\n"
    return command

def fileize_command(command: str):
    with open("/home/ubuntu/temp_command.sh", "w") as f:
        f.write("#!/bin/bash -l \n")
        f.write(command)
    return "/home/ubuntu/temp_command.sh"

def send_command(process, command, get_output=False):
    global magic_string
    new_command = convert_command(command)
    print("Sending command: " + command)
    print(new_command)
    process.stdin.write(new_command.encode("utf-8"))
    process.stdin.flush()
    # if get_output:
    #     output = ""
    #     while True:
    #         line = process.stdout.readline().decode("utf-8")
    #         if line == '' and process.poll() is not None:
    #             break
    #         if line:
    #             print("Line: ", line.strip())
    #             if magic_string in line:
    #                 break
    #             if "\r" in line:
    #                 print("R string", line.strip())
    #                 continue
    #             output += line.strip() + "\n"
    #             print(line.strip())
    #     return output


def test(command, working_directory: str) -> (int, str):
    global magic_string
    print("Running command: " + command)
    command_file = fileize_command(command)
    subprocess.run(["chmod", "+x", command_file])
    process = subprocess.Popen([command_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=working_directory)
    output_lines = []
    while True:
        # print("Waiting for line")
        line = process.stdout.readline().decode("utf-8")
        if not line:
            break
        # if line == '' and process.poll() is not None:
        #     break
        if line:
            print(line.strip())
            if line == '' and process.poll() is not None:
                break
            # if magic_string in line:
            #     return_code = int(line.split(magic_string)[0].strip())
            #     return return_code, "\n".join(output_lines)
            if '\r' in line:
                continue
            output_lines.append(line.strip())
    process.wait()
    return_code = process.poll()
    process.kill()
    return return_code, "\n".join(output_lines)

def execute_commands(yaml_commands, working_directory: str):
    command_data = []
    for command in yaml_commands:
        data = {
            "name": command["name"],
            "command": "",
            "reference_output": "",
            "analysis_method": command["analysis_method"] if "analysis_method" in command else None,
            "parse_options": command["parse_options"] if "parse_options" in command else {},
        }
        if data["analysis_method"] == "return_code":
            data["command"] = "set -e\n"

        for env_command in global_environment:
            data["command"] += env_command + "\n"
        local_environment = command["environment"] if "environment" in command else []
        for env_command in local_environment:
            data["command"] += env_command + "\n"
        if type(command["commands"]) == str:
            command["commands"] = [command["commands"]]
        for line in command["commands"]:
            data["command"] += line + "\n"
        print("Running ", command["name"], flush=True)
        return_code, reference_output = test(data["command"], working_directory)
        data["reference_output"] = reference_output
        command_data.append(data)
    return command_data

try:
    # get argument TIMES_RUN
    times_run = int(sys.argv[1])
    repo_name_escaped = repo_name.replace("/", ",")
    if times_run == 0:
        # first clone the repository
        # print("Cloning repository...")
        # print(f"git clone https://github.com/{repo_name}.git {repo_name_escaped}")
        # subprocess.run(f"git clone https://github.com/{repo_name}.git {repo_name_escaped}", shell=True)
        subprocess.run(f"mkdir {repo_name_escaped}", shell=True)

        # TODO: change subprocess.PIPE to sys.stdout on all lines
        execute_commands(yaml_data["pre_commands"], f"{repo_name_escaped}")

        # create zip archive of the repository
        # print("Zipping repository...")
        # subprocess.run(["zip", "-r", "-q", f"{repo_name_escaped}.zip", f"{repo_name_escaped}"])
        # print("Zipping finished")
        exit(0)

    if yaml_data["build_commands"] is not None:
        build_commands = execute_commands(yaml_data["build_commands"], f"{repo_name_escaped}")
    else:
        build_commands = []

    if yaml_data["run_commands"] is not None:
        print(yaml_data["run_commands"])
        run_commands = execute_commands(yaml_data["run_commands"], f"{repo_name_escaped}")
    else:
        raise Exception("No run commands specified")

# except KeyboardInterrupt:
#     print("Keyboard interrupt, exiting")
#     sys.exit(1)
except Exception as e:
    print("Exception occurred, exiting")
    print(e)
    sys.exit(1)

print("Build and run commands finished, outputs captured, preparing to upload to S3")
json_obj = {
    "repo_name": repo_name,
    "build_commands": build_commands,
    "run_commands": run_commands,
    "build_time": time.time(),
}

# Upload the json object to S3
s3 = boto3.resource('s3')
s3.Bucket(bucket).put_object(Key=f"outputs/{repo_name}.json", Body=json.dumps(json_obj))
print("JSON object uploaded to S3")

# Upload the zipped archive to S3
# s3.Bucket('gersteincodegenprod').upload_file(f"{repo_name_escaped}.zip", f"repos/{repo_name_escaped}.zip")
# print("Zip archive uploaded to S3")

print("REPO_NAME: ", repo_name.replace("/", "_")) # used to return the tag for the docker image
