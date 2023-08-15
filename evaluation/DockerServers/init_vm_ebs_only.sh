#!/bin/bash

# THIS SCRIPT IS MEANT FOR VMS WITHOUT LOCAL SSDS

# Use the following command in EC2 user data to initialize the VM for the first time.
# #!/bin/bash
# curl -s http://gersteincodegenprod.s3.amazonaws.com/init_vm_ebs_only.sh | sudo bash

# This script is used to initialize the VM for the first time.
sudo apt update
sudo apt install -y openjdk-11-jdk bzip2 build-essential libncurses5-dev bzip2 build-essential libncurses5-dev libbz2-dev liblzma-dev python3-pip git wget sudo
sudo apt install zip unzip python3-venv python3-dev python3-pip python3-setuptools python3-wheel python-is-python3 -y
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



# HTSGET-specific
# cd /home/ubuntu/ || exit
# sudo -u ubuntu wget http://gersteincodegenprod.s3.amazonaws.com/repos/samtools,htsjdk.zip -O htsjdk.zip
# sudo -u ubuntu unzip htsjdk.zip
# #sudo -u ubuntu git clone https://github.com/samtools/htsjdk.git
# #cd htsjdk || exit
# #sudo -u ubuntu git checkout 8108d56ad8894ecb7840788340ced2ebc60e152c
# cd /home/ubuntu/samtools,htsjdk || exit
# #sudo -u ubuntu ./scripts/install-samtools.sh
# sudo -u ubuntu ./scripts/htsget-scripts/start-htsget-test-server.sh




sudo -u ubuntu pip3 install bs4 requests pyyaml docker

# ADD ANY OTHER REPOSITORY-SPECIFIC INITIALIZATION HERE

#sudo apt update && sudo apt install mdadm --no-install-recommends -y
#sudo mdadm --create /dev/md0 --level=0 --raid-devices=4 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1 /dev/nvme4n1
#sudo mkfs.ext4 -F /dev/md0
#sudo mkdir -p /mnt/disks/codegen_data
#sudo mount /dev/md0 /mnt/disks/codegen_data
#sudo chmod a+w /mnt/disks/codegen_data
#
#printf "\{\n\"data-root\": \"/mnt/newlocation\"\n\}" >> /etc/docker/daemon.json
#sudo service docker restart
cd /home/ubuntu || exit
#sudo -u ubuntu wget https://storage.lilbillbiscuit.com/start_test.py
#sudo -u ubuntu wget https://storage.lilbillbiscuit.com/Dockerfile_Generalized -O Dockerfile
sudo -u ubuntu wget https://gersteincodegenprod.s3.amazonaws.com/docker_runner.py
#sudo -u ubuntu docker build -t htsjdktest .

# get number of cores in the VM
CORES=$(nproc --all)
# take 80% of the cores as an integer
CORES=$(echo "$CORES * 0.85 / 1" | bc)


sudo cat <<EOF | sudo tee /etc/systemd/system/passatk.service
[Unit]
Description=Python Tester
After=multi-user.target

[Service]
Type=simple
User=ubuntu
Restart=no
ExecStart=/usr/bin/python3 /home/ubuntu/docker_runner.py $CORES
Environment=PROD=true


[Install]
WantedBy=multi-user.targetdocker
EOF

sudo systemctl daemon-reload
sudo systemctl start passatk.service

