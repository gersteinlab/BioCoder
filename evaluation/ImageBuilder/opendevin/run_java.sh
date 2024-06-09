#!/bin/bash

file_path="$1"

dir_path=$(dirname $file_path)
file_name=$(basename $file_path)
class_name="${file_name%.*}"
class_file_name="$class_name.class"

cd $dir_path

if [ ! -e "$class_file_name" ]; then
    javac -cp /testing/sources/java/commons-math3-3.6.1.jar:/testing/sources/java/htsjdk-e525172-SNAPSHOT.jar:/testing/sources/java/jregex1.2_01.jar $file_name
fi

java -cp .:/testing/sources/java/commons-math3-3.6.1.jar:/testing/sources/java/htsjdk-e525172-SNAPSHOT.jar:/testing/sources/java/jregex1.2_01.jar $class_name
