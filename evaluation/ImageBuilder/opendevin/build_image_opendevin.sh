#!/bin/bash -xe

ORIGINAL_LOCATION=$PWD
cd ~/opendevin_base
docker build -t public.ecr.aws/i5g0m1f6/eval_biocoder:base .
docker push public.ecr.aws/i5g0m1f6/eval_biocoder:base

cd $ORIGINAL_LOCATION


# Define the name of the Docker image

BASE_IMAGE_NAME="passatkrunner"
S3_BUCKET_NAME="gersteincodegenprod"
DOCKER_REPOSITORY_URL="public.ecr.aws/i5g0m1f6"



# Write the Dockerfile
cat > Dockerfile <<EOF
FROM public.ecr.aws/i5g0m1f6/eval_biocoder:base
USER devin
WORKDIR /home/devin
RUN sudo mkdir -p /testing && sudo mkdir -p /testing_files && sudo chown -R devin:devin /testing_files && sudo chown -R devin:devin /testing
USER root

RUN mamba create -n test python=3.6 -y && mamba init bash
RUN wget https://gersteincodegenprod.s3.amazonaws.com/general/requirements.txt
RUN mamba run -n test python -m pip install -r requirements.txt

USER devin
COPY sources/ /testing
COPY fuzzer_tester.py /testing
COPY start_test_opendevin.py /testing
COPY run_java.sh /testing

USER root

CMD ["bash", "-c", "mamba run -n test python3 start_test.py"]
EOF

# Add any other scripts needed to be run here

ALL_IMAGE_NAME="${DOCKER_REPOSITORY_URL}/eval_biocoder:v1.0"
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ALL_IMAGE_NAME

# Build the Docker image
docker build -t $ALL_IMAGE_NAME --progress=plain --no-cache .

# Run the Docker container
#docker run -it --network="host" $ALL_IMAGE_NAME python3 build_docker_image.py 0
echo "Pushing image to ECR"
docker push $ALL_IMAGE_NAME


# Remove the Dockerfile
rm Dockerfile

