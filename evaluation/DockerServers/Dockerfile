FROM ubuntu:focal
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y openjdk-17-jdk bzip2 build-essential libncurses5-dev bzip2 build-essential libncurses5-dev libbz2-dev liblzma-dev python3-pip git wget sudo zip unzip curl
RUN useradd -ms /bin/bash ubuntu
# give ubuntu sudo access without password
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER ubuntu
WORKDIR /home/ubuntu
# Install adoptium jdk 17 
RUN wget https://gersteincodegenprod.s3.amazonaws.com/binaries/adoptium17-jdk.tar.xz -O adoptium17-jdk.tar.xz && tar -xf adoptium17-jdk.tar.xz && rm adoptium17-jdk.tar.xz
ENV JAVA_HOME=/home/ubuntu/jdk-17.0.6+10/
ENV PATH=$JAVA_HOME/bin:$PATH
ENV PATH=/home/ubuntu/mambaforge/bin:$PATH
ENV ENV_NAME="base"
RUN wget -O Mambaforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
RUN bash Mambaforge.sh -b -p /home/ubuntu/mambaforge
RUN ~/mambaforge/condabin/conda init && ~/mambaforge/condabin/mamba init

RUN pip3 install --upgrade pip
RUN pip3 install bs4 requests pandas numpy scipy matplotlib seaborn tqdm boto3 pyyaml
RUN wget http://gersteincodegenprod.s3-website-us-east-1.amazonaws.com/start_test.py -O start_test.py && chmod +x start_test.py
RUN wget http://gersteincodegenprod.s3-website-us-east-1.amazonaws.com/fuzzer/fuzzer_tester.py -O fuzzer_tester.py && chmod +x fuzzer_tester.py
RUN echo "export PS1='\u:\W\$ '" >> /home/ubuntu/.bashrc

CMD ["bash", "-c", "python3 start_test.py"]
