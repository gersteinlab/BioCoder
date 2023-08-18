"""
The script facilitates the distribution and organization of various
files needed for different components and tools by uploading them to an S3 bucket.
This process helps in ensuring that the required resources are readily available
for the respective components of a larger system.
"""

import boto3

s3 = boto3.client('s3')
s3_bucket = "gersteincodegenprod"

# ImageBuilder
s3.upload_file("ImageBuilder/start_test.py", s3_bucket, "start_test.py")
s3.upload_file("ImageBuilder/build_docker_image.py", s3_bucket, "build_docker_image.py")
s3.upload_file("ImageBuilder/build_image.sh", s3_bucket, "build_image.sh")
s3.upload_file("ImageBuilder/requirements.txt", s3_bucket, "general/requirements.txt")
s3.upload_file("ImageBuilder/init_build_environment.sh", s3_bucket, "init_build_environment.sh")

# DockerServers
s3.upload_file("DockerServers/init_vm_ebs_only.sh", s3_bucket, "init_vm_ebs_only.sh")
s3.upload_file("DockerServers/Dockerfile", s3_bucket, "Dockerfile")
s3.upload_file("DockerServers/docker_runner.py", s3_bucket, "docker_runner.py")

# Fuzzer
s3.upload_file("Fuzzer/fuzzer_tester.py", s3_bucket, "fuzzer/fuzzer_tester.py")
s3.upload_file("Fuzzer/run_java.sh", s3_bucket, "fuzzer/run_java.sh")

# LLMGeneration
s3.upload_file("../LLMGeneration/codetf_generation/batch_run_codetf.py", s3_bucket, "batch_run_codetf.py")
s3.upload_file("../LLMGeneration/codetf_generation/init_codetf.sh", s3_bucket, "init_codetf.sh")
s3.upload_file("../LLMGeneration/codetf_generation/init_codetf_alt.sh", s3_bucket, "init_codetf_alt.sh")
s3.upload_file("../LLMGeneration/codetf_generation/runcodetf.py", s3_bucket, "runcodetf.py")
s3.upload_file("../LLMGeneration/codetf_generation/final_batch_run.py", s3_bucket, "final_batch_run.py")
print("Finished uploading files")