#!/bin/bash

#PRJ_DIR=/base
DREAM_DIR=$(dirname "$(readlink -f "$0")")

# Start trade service
python3 ${DREAM_DIR}/common/dream_service.py &

#python3 ${DREAM_DIR}/input/dog_info.py --market cn &

#python3 script2.py &
#python3 script3.py &

wait