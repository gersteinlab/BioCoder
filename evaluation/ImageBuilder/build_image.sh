#!/bin/bash -xe

# Define the name of the Docker image

# check if --prod flag is passed
if [[ $1 == "--prod" ]]; then
    echo "prod flag found"
    IMAGE_NAME="passatkrunner"
    S3_BUCKET_NAME="gersteincodegenprod"
    ENVIRONMENT_COMMAND="PROD=true"
else
    echo "prod flag not found"
    IMAGE_NAME="passatkrunnertest"
    S3_BUCKET_NAME="gersteincodegentest"
    ENVIRONMENT_COMMAND="TESTING=true"
fi
DOCKER_REPOSITORY_URL="public.ecr.aws/i5g0m1f6"



# Write the Dockerfile
cat > Dockerfile <<EOF
FROM $DOCKER_REPOSITORY_URL/$IMAGE_NAME:base
USER ubuntu
WORKDIR /home/ubuntu
COPY build_docker_image.py build_docker_image.py
COPY build_data.yaml build_data.yaml
RUN wget http://$S3_BUCKET_NAME.s3-website-us-east-1.amazonaws.com/start_test.py -O start_test.py && chmod +x start_test.py
RUN wget http://$S3_BUCKET_NAME.s3-website-us-east-1.amazonaws.com/fuzzer/fuzzer_tester.py -O fuzzer_tester.py && chmod +x fuzzer_tester.py
RUN $ENVIRONMENT_COMMAND python3 build_docker_image.py 0
CMD ["bash", "-c", "mamba run -n test $ENVIRONMENT_COMMAND python3 start_test.py"]
EOF

# Add any other scripts needed to be run here

cat > get_yaml.py <<EOF
import yaml

with open("build_data.yaml", "r") as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        exit(1)

print(data["repo_name"].replace("/", "_"))
EOF

REPO_NAME_ESCAPED=$(python3 get_yaml.py)
rm get_yaml.py

# check if repo contains htsjdk
if [[ $REPO_NAME_ESCAPED == *"htsjdk"* ]]; then
    echo "htsjdk found"
    # clone htsjdk, ignore if already cloned
    if [ ! -d "htsjdk" ]; then
        git clone https://www.github.com/samtools/htsjdk.git
    fi
    cd htsjdk || exit
    ./scripts/install-samtools.sh
    ./scripts/htsget-scripts/start-htsget-test-server.sh
    cd ..
fi

ALL_IMAGE_NAME="${DOCKER_REPOSITORY_URL}/${IMAGE_NAME}:${REPO_NAME_ESCAPED}"
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ALL_IMAGE_NAME

# Build the Docker image
docker build -t $ALL_IMAGE_NAME --progress=plain --no-cache .

# Run the Docker container
#docker run -it --network="host" $ALL_IMAGE_NAME python3 build_docker_image.py 0
echo "Pushing image to ECR"
docker push $ALL_IMAGE_NAME
echo "Running image"
docker run -it -e $ENVIRONMENT_COMMAND --network="host" $ALL_IMAGE_NAME python3 build_docker_image.py 1

# Remove the Dockerfile
rm Dockerfile

