#!/bin/bash

#PRJ_DIR=/base
DREAM_DIR=$(dirname "$(readlink -f "$0")")

# Start service
python3 ${DREAM_DIR}/${SERVICE_LOCATION}/service.py &

#python3 ${DREAM_DIR}/input/dog_info.py --market cn &

#python3 script2.py &
#python3 script3.py &

wait