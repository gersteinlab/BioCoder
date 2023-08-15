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

java_context_path_base = '/home/ubuntu/CodeGen/BCE/Java/Context'
java_golden_path_base = '/home/ubuntu/CodeGen/BCE/Java/GoldenCode'

python_context_path_base = '/home/ubuntu/CodeGen/BCE/GenerateTesting/Context'
python_golden_path_base = '/home/ubuntu/CodeGen/BCE/GenerateTesting/GoldenCode'


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

def run(model_name, version, dataset, generated_path_base):
    if dataset == "Java":
        context_path_base = java_context_path_base
        golden_path_base = java_golden_path_base
    elif dataset == "Python":
        context_path_base = python_context_path_base
        golden_path_base = python_golden_path_base

    count=0
    
    for filename in os.listdir(golden_path_base):
      
        context_path = context_path_base +"/"+ filename
        generated_path = generated_path_base +"/"+ filename
        golden_path = golden_path_base + "/"+filename
        
        if not os.path.exists(generated_path):
            print(f"Generated path {generated_path} does not exist")
            continue
        if not os.path.exists(golden_path):
            print(f"Golden path {golden_path} does not exist")
            continue
        if not os.path.exists(context_path):
            print(f"Context path {context_path} does not exist")
            continue

        # check if path exists in ZipFiles
        zip_base = f'/home/ubuntu/CodeGen/BCE/GenerateTesting/ZipFiles/{model_name}/{version}'
        
        if not os.path.exists(zip_base):
            os.makedirs(zip_base)
        try:
    
            test_case_id = model_name + "-" + version + "-" + dataset + "-" +  filename.split(".")[0]
            zip_path = f'/{zip_base}/{test_case_id}.zip'
            
            with zipfile.ZipFile(zip_path, 'w') as zipObj:
                
                if dataset == "Java":
                    # indicates that this is a java test case
                    zipObj.write(context_path, arcname="context.java")
                    zipObj.write(generated_path, arcname="generated.java")
                    zipObj.write(golden_path, arcname="golden.java")
                    
                    
                if dataset == "Python":
                    zipObj.write(context_path, arcname="context.py")
                    zipObj.write(generated_path, arcname="generated.py")
                    zipObj.write(golden_path, arcname="golden.py")
                    
        except Exception as e:
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
            "num_tests": 4,
        }

        r = requests.post(f"{baseUrl}/add", json=request_payload)
        count += 1
        print(f"{model_name}: {dataset}: Count: {count} of {len(os.listdir(golden_path_base))}")
        
    print(f"{model_name}: {dataset}: Added {count} test cases to the queue")
    return count

def run_proxy(obj):
    path_name, dataset_name = obj
    version = path_name.split("/")[-1]
    author = path_name.split("/")[-3]
    model_name2 = path_name.split("/")[-2]
    run(model_name2, version, dataset_name, path_name) 
    

import multiprocessing

if __name__ == '__main__':
    java_url = "/home/ubuntu/CodeGen/BCE/Java/GeneratedCode"
    python_url= "/home/ubuntu/CodeGen/BCE/GenerateTesting/GeneratedCode"
    obj = (java_url, "Java")
    run_proxy(obj)