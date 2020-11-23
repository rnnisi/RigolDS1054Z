#!/bin/bash 
# make server to upload data on 

sudo apt-get update

sudo apt-get install apache2

sudo apt-get install php libapache2-mod-php

sudo chmod a+w /var
sudo chmod a+w /var/www
sudo chmod a+w /var/www/html/

mkdir /var/www/html/RIGOL

sudo chmod a+w /var/www/html/RIGOL

