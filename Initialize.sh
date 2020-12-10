#!/bin/bash

read -p "Enter the number of channels the scope has as an integer : " CHANNELS
CHANNELS="$CHANNELS"
read -p "Enter the serial number of the scope : " SERIAL
SERIAL="$SERIAL" 
read -p "Enter a nickname for this scope/pi pair : " NICKNAME
NICKNAME="$NICKNAME"

sed -i 's/CHANNELS/'$CHANNELS/ RigolDS1000Z.py
sed -i 's/SERIAL/'$SERIAL/ RigolDS1000Z.py
sed -i 's/NICKNAME/'$NICKNAME/ RigolDS1000Z.py
sed -i 's/NICKNAME/'$NICKNAME/ SetupServer.sh
sed -i 's/NICKNAME/'$NICKNAME/ DataTransfer.py
