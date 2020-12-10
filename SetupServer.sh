#!/bin/bash 
# make server to upload data on 

sudo apt-get update

sudo apt-get install apache2

sudo apt-get install php libapache2-mod-php

sudo chmod a+w /var
sudo chmod a+w /var/www
sudo chmod a+w /var/www/html/

mkdir /var/www/html/NICKNAME

sudo chmod a+w /var/www/html/NICKNAME
EXPLOG="/var/www/html/NICKNAME/ExpLog.php"
echo "<!DOCTYPE html>" > $EXPLOG
echo "<html>" >> $EXPLOG
echo "<body>" >> $EXPLOG
echo "<h1>Experiment Log</h1>" >> $EXPLOG
echo '<?php echo "INSERT"; ?><br>' >> $EXPLOG
echo "</body>" >> $EXPLOG
echo "</html>" >>$EXPLOG
