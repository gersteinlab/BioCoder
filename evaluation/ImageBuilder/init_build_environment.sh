#!/bin/bash

# Use the following command in EC2 user data to initialize the VM for the first time.
# #!/bin/bash
  # curl -s http://gersteincodegenprod.s3.amazonaws.com/init_build_environment.sh | sudo bash

# This script is used to initialize the VM for the first time.
sudo apt update
sudo apt install -y openjdk-11-jdk bzip2 build-essential libncurses5-dev bzip2 build-essential libncurses5-dev libbz2-dev liblzma-dev python3-pip git wget sudo
sudo apt install zip unzip -y
sudo -u ubuntu wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /home/ubuntu/miniconda.sh
sudo -u ubuntu bash /home/ubuntu/miniconda.sh -b -p /home/ubuntu/miniconda
# install docker
sudo apt-get remove docker docker-engine docker.io containerd runc -y
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release -y
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo usermod -aG docker ubuntu

sudo -u ubuntu pip3 install --upgrade pip
sudo -u ubuntu pip3 install bs4 requests boto3 pyyaml

# install aws cli
cd /home/ubuntu || exit
sudo -u ubuntu curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo -u ubuntu unzip awscliv2.zip
sudo -u ubuntu sudo ./aws/install
# remove aws cli temporary install files
sudo -u ubuntu rm -rf /home/ubuntu/awscliv2.zip /home/ubuntu/aws

sudo -u ubuntu aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/i5g0m1f6

# download build files
sudo -u ubuntu wget https://gersteincodegenprod.s3.amazonaws.com/build_docker_image.py -O /home/ubuntu/build_docker_image.py
sudo -u ubuntu wget https://gersteincodegenprod.s3.amazonaws.com/build_image.sh -O /home/ubuntu/build_image.sh
sudo -u ubuntu wget https://gersteincodegenprod.s3.amazonaws.com/build_data.yaml -O /home/ubuntu/build_data.yaml