#!/bin/bash

# limit the number of threads to 1, memory to 7G, time to 60 seconds
ulimit -t 60 -v 7000000

python3 $1
