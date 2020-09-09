#!/bin/bash
# Rebecca Nishide, 09/08/2020 
# contact: rnnishide@gmail.com for key


# check for lxi 
LXI=$(which -a lxi)
echo $LXI
LXII=$"true"
if [[ "$LXI" == "lxi not found" ]]
then
    LXII=$"false"
fi

if [[ "$LXI" == '' ]]
then
    LXII=$"false"
fi

if [[ "$LXII" == "false" ]]
then
    echo "lxi not installed"
    echo "lxi is optional... keep going"
    echo ""
fi

# check for python3
PYTHON=$(which -a python3)
echo $PYTHON
if [[ "$PYTHON" == "" ]]
then
    echo "make sure python3 is installed properly"
    exit
fi

echo "python3 requirement satisfied"

# get pyvisa, other lib already included 
sudo pip3 install pyvisa
sudo pip3 install pyvisa-py

# clone from github with https 
# need to request access from me to use. 

git clone https://github.com/rnnisi/RigolDS1054Z.git
