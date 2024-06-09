FROM $DOCKER_REPOSITORY_URL/$IMAGE_NAME:base
USER ubuntu
WORKDIR /home/ubuntu
COPY build_docker_image.py build_docker_image.py
COPY build_data.yaml build_data.yaml
RUN wget http://$S3_BUCKET_NAME.s3-website-us-east-1.amazonaws.com/start_test.py -O start_test.py && chmod +x start_test.py
RUN wget http://$S3_BUCKET_NAME.s3-website-us-east-1.amazonaws.com/fuzzer/fuzzer_tester.py -O fuzzer_tester.py && chmod +x fuzzer_tester.py
RUN $ENVIRONMENT_COMMAND python3 build_docker_image.py 0
CMD ["bash", "-c", "mamba run -n test $ENVIRONMENT_COMMAND python3 start_test.py"]