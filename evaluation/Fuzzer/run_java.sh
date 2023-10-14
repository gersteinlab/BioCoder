#!/bin/bash

file_path="$1"

dir_path=$(dirname $file_path)
file_name=$(basename $file_path)
class_name="${file_name%.*}"
class_file_name="$class_name.class"

cd $dir_path

if [ ! -e "$class_file_name" ]; then
    # Replace with paths to Java packages
    javac -cp /home/ubuntu/CodeGen/commons-math3-3.6.1/commons-math3-3.6.1.jar:/home/ubuntu/CodeGen/htsjdk-3.0.5/build/libs/htsjdk-e525172-SNAPSHOT.jar:/home/ubuntu/CodeGen/jregex1.2_01.jar $file_name
fi
# Replace with paths to Java packages
java -cp .:/home/ubuntu/CodeGen/commons-math3-3.6.1/commons-math3-3.6.1.jar:/home/ubuntu/CodeGen/htsjdk-3.0.5/build/libs/htsjdk-e525172-SNAPSHOT.jar:/home/ubuntu/CodeGen/jregex1.2_01.jar $class_name
