"""
This script generates test cases for code prompts,
packages them into zip files, uploads them to S3, and notifies an
API service about the added test cases for further processing.
It uses multiprocessing for efficiency and is designed to operate in
different environments based on environment variables.
"""

import os
from tqdm import tqdm
import requests
import boto3
import json
import zipfile

cnt = 1
startAt = 146
s3bucket = "gersteincodegenprod"
s3prefix = "functions"
s3 = boto3.client('s3')

model_name = "codegen-6B-mono"

version = "v2"
dataset="Java"


# java_context_path_base = '/home/ubuntu/CodeGen/BCE/Results/Prompts/Java/Context'
# java_golden_path_base = '/home/ubuntu/CodeGen/BCE/Results/Prompts/Java/GoldenCode'

# python_context_path_base = '/home/ubuntu/CodeGen/BCE/Results/Prompts/Python/Context'
# python_golden_path_base = '/home/ubuntu/CodeGen/BCE/Results/Prompts/Python/GoldenCode'
java_context_path_base = '/output/Prompts/Java/Context' # Path to Java context
java_golden_path_base = '/output/Prompts/Java/GoldenCode' # Path to Java golden code

python_context_path_base = '/output/Prompts/Python/Context' # Path to Python context
python_golden_path_base = '/output/Prompts/Python/GoldenCode' # Path to Python golden code



if "TESTING" in os.environ:
    baseUrl = "https://fhdsxjdwjuo4chghz7mlaw2cju0ppwfx.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegenprod"
    ecr_repo = "passatkrunner"
elif "PROD" in os.environ:
    baseUrl="https://wnn2rjzzw2nkqj6yfbbp5igfmy0yxemy.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegentest"
    ecr_repo = "passatkrunnertest"
else:
    raise Exception("No environment variable set")

def run(model_name, version, dataset, generated_path_base, prompt_type):
    if dataset == "Java":
        context_path_base = java_context_path_base
        golden_path_base = java_golden_path_base
    elif dataset == "Python":
        context_path_base = python_context_path_base
        golden_path_base = python_golden_path_base

    count=0
    for filename in os.listdir(golden_path_base):
        if dataset == "Java":
            temp = filename.replace(".java", ".txt")
        elif dataset == "Python":
            temp = filename.replace(".py", ".txt")
        context_path = context_path_base +"/"+ filename
        generated_path = generated_path_base +"/"+ temp
        golden_path = golden_path_base + "/"+filename
        
        if not os.path.exists(generated_path):
            # try generated path without .txt
            generated_path = generated_path_base +"/"+ filename.split(".")[0]
            if not os.path.exists(generated_path):
                print(f"Generated path {generated_path} does not exist")
                continue
        if not os.path.exists(golden_path):
            print(f"Golden path {golden_path} does not exist")
            continue
        if not os.path.exists(context_path):
            print(f"Context path {context_path} does not exist")
            continue
        
        # generated path should be a directory
        generated_files = os.listdir(generated_path)
        
        for i in range(len(generated_files)):
            # look for file 0
            if not os.path.exists(generated_path+"/"+str(0)):
                file_index = i+1
            else:
                file_index = i
            # check if path exists in ZipFiles
            zip_base = f'/home/ubuntu/CodeGen/BCE/GenerateTesting/ZipFiles/{model_name}/{version}'
            
            if not os.path.exists(zip_base):
                os.makedirs(zip_base)
            try:
        
                test_case_id = f"{model_name}-{version}-{dataset}-{prompt_type}-{filename.split('.')[0]}-{i}"
                zip_path = f'/{zip_base}/{test_case_id}.zip'
                
                with zipfile.ZipFile(zip_path, 'w') as zipObj:
                    
                    if dataset == "Java":
                        # indicates that this is a java test case
                        zipObj.write(context_path, arcname="context.java")
                        zipObj.write(generated_path+"/"+str(file_index), arcname="generated.java")
                        zipObj.write(golden_path, arcname="golden.java")
                        
                        
                    if dataset == "Python":
                        zipObj.write(context_path, arcname="context.py")
                        zipObj.write(generated_path+"/"+str(file_index), arcname="generated.py")
                        zipObj.write(golden_path, arcname="golden.py")
                        
            except Exception as e:
                # if exception type is file not found
                print(e)
                continue

            # get filename portion of zip path
            zip_filename = zip_path.split("/")[-1]

            
            # upload to s3
            s3.upload_file(zip_path, s3bucket, f'{s3prefix}/{test_case_id[0]}/{zip_filename}')
            
            request_payload = {
                "test_case_repo": "lilbillybiscuit/323tester",
                "file": filename,
                "filePath": "none",
                "lineStart": 0,
                "lineEnd": 0,
                "test_case_id": test_case_id,
                "methodBody": "none",
                "num_tests": 50,
            }

            r = requests.post(f"{baseUrl}/add", json=request_payload)
        count += 1
        print(f"{model_name}: {dataset}: Count: {count} of {len(os.listdir(golden_path_base))}")
        
    print(f"{model_name}: {dataset}: Added {count} test cases to the queue")
    return count

def run_proxy(model_name):
    print(f"Running {model_name}")
    version = model_name.split("/")[-3]
    author = model_name.split("/")[-5]
    model_name2 = model_name.split("/")[-4]
    dataset_name = model_name.split("/")[-2]
    prompt_type = model_name.split("/")[-1]
    if dataset_name not in ["Java", "Python"]:
        return
    
    return run(model_name2, version, dataset_name, model_name, prompt_type) 
    

import multiprocessing

if __name__ == '__main__':
    base_url = "/output"
    model_names = []
    # get all directories exactly 4 folders deep from base_url
    for root, dirs, files in os.walk(base_url):
        levels_deep = root.count(os.path.sep) - base_url.count(os.path.sep)
        if levels_deep == 5:
            model_names.append(root)

    # dataset_names = ["Java", "Python"]

    # run_package = []
    # for model_name in model_names:
    #     for dataset_name in dataset_names:
    #         run_package.append((model_name, dataset_name))

    # run_proxy(run_package[0])

    with multiprocessing.Pool(16) as p:
        total_count = p.map(run_proxy, model_names)
    sum_count = 0
    for i in range(len(total_count)):
        if total_count[i] is not None:
            sum_count += total_count[i]
    print(f"Added {sum_count} test cases to the queue")
