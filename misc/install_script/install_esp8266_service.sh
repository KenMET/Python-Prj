#!/bin/bash

#Copy first
sudo cp ${PYTHON_ROOT}/systemd/esp8266_server.service /lib/systemd/system

#Modify path
CURRENT_PATH=`pwd`
PYTHON_ROOT=${CURRENT_PATH%/*}
TEMP="'s/xxxxxxxxxx/${PYTHON_ROOT//\//\\\/}/g'"
COMM="sudo sed -i ${TEMP} /lib/systemd/system/esp8266_server.service"
eval ${COMM}

sudo systemctl enable /lib/systemd/system/esp8266_server.service
sudo systemctl start esp8266_server.service
sudo systemctl status esp8266_server.service
