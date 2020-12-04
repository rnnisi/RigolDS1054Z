# RigolDS1054Z


## Purpose
This program pulls waveforms from a Rigol DS1054Z scope using python with no backend or driver, over localhost or USB interface. Data collection through USB requires root ability. Program is intended to allow researcher to set it up and leave to collect data on a raspberry pi. Rapberry pi can then be controlled remotely to start program or check status, although depending on desired functionality, user may need to be present to change settings on scope. Each experiment is recorded in an Experimental Log test file, and yields numbered CSV files (one for each waveform) as well as a log of the program activity over the course of the experiment. Practical error handling is written in; program is responsive to all the issues and circumstances I could personally think of.

This program can be utilized for any of the three trigger settings the Rigol DS1054Z scope offers; auto, force, or single. To cut down on time, the program writes data out to a raw data file initially, and then processes that file into readable CSV's after collection has stopped. 

get_RigolDS1054Z will automatically check the OS and install requirements. It will make a new directory which contains the contents of this repo. Potential users can email me (rnnishide@gmail.com) for their pub-keys to be approved for deployment. 

This repository includes code for data transfer. The data transfer method operates by using the Rapberry Pi as a local server. Scripts for upload and download from a local site are provided. User should be aware of memory space on the Pi and delete files manually as needed once they have been transferred for analysis; no built in removal functions are given. 

## Program Configuration and Requirements
This program is meant to be run on a Linux OS on a Rapberry Pi with python3.
Make sure scope is configured correctly for desired data acquisiton method, as described in Acqusition Options and Implementation section.

On the scope, Utility -> LAN Config -> Configure needs to be on DHCP and Auto, so that IP adress indicates localhost.
Utility -> LAN Config -> RemoteIO LAN needs to be "on" 

Root ability or new device rules are required to use USB interface for data acquisition. 

### Python Libraries 
- pyvisa
- time
- os
- sys
- subprocess
- threading
- _thread
- multiprocessing

### Optional software
- lxi-tools (requires API and peripheral software, see https://lxi-tools.github.io/) 

## Contents
### RigolDS1054Z.py
library for DAQ from scope. Will work with similar Rigol scopes

### ExpLog.txt 
Track runs

### remember_IP.txt
Embeded file which contains the SCPI address which was used for the last sucessful connection
  
### plot.py
Run in directory with data csv files : ./plot.py <waveform number>. Script will plot all waveform csv's under same experimental number, takes number of waveform as command line arguement. Deploy in Exp_n directory to plot Wfm_i.csv

### DataTransfer.py
Library for data transfer, allows use of Raspberry-Pi as a server for data hand-off. 

### SetupServer.sh
Will install necessary software to use raspberry-pi as server and update permissions. Use root to run.

### UPLOAD.py
Run in directory on Pi used to collect data from working directory containing Exp_n files. Give experiment number "n" values as command line arguements. The script will upload each directory "Exp_n' and its contents to a local site. 

### DOWNLOAD.py
Run in terminal of device intended for analysis, which is connected to same local network as pi used to collect data. This script will download and decode all the data from the local site for analysis. Again, give experiment "n", as in "Exp_n", to specifiy which experiment you want to download data for. This script will set up a new "Exp_n" data file in the working directory from which it is run. 


### Run Scripts: See following section.

## Acqusition Options and Implementation

The provided run scripts take command line arguements which must be inputted correctly by the user to be accepted. 

The zeroth arguement is the name of the run script, which is detailed below. 

The first arguement should be the run time in seconds. The run time will dictate how long you want to collect data for. User can always end run early with ^C, and program will continue to processing. 

The second arguement should dictate trigger setting. <AUTO> will set trigger to auto, <FORCE> will force the trigger with every collection, and <X.XV> will set the trigger to X.X V for single trigger mode. mV or uV units may also be used. Numerical trigger value must be followed by units; no space. For single trigger mode, the program will sit and wait until the scope is triggered. Waveforms will only be collected when the scope is triggered. Only when waveforms are collected will the scope be wllowed to run again.  The status of the trigger with each check will be recorded with the corresponding time. 
  
Additional arguements should be integer values 1-4 to specificy which channels data should be read from. If no channel specifications are given, the program will read all four channels. Anywhere between one and four channels can be read, although the channels cannot be read simultaneously; more channels means each acqusition is longer. 

### 1.	LAN_Run.py
Run with <./LAN_Run.py> <RunTime> <TriggerSet> to acquire data over local network shared by Raspbery Pi and scope. Make sure that scope DHCP is enabled on scope. 

On the scope, Utility -> IO Setting -> LAN Config -> Configure needs to be on DHCP and Auto, so that IP adress indicates localhost.
Utility -> IO Setting -> LAN Config -> RemoteIO LAN needs to be "on" 

### 2.	LXI_Run.py
Run with <./LXI_Run.py> <RunTime> <TriggerSet> to acquire data using LXI tools. This of course will only work if LXI tools is properly installed. This method may be faster or give less connection issues. This program still uses SCPI commands for initialization. 

On the scope, Utility -> IO Setting -> LAN Config -> Configure needs to be on DHCP and Auto, so that IP adress indicates localhost.
Utility -> IO Setting -> LAN Config -> RemoteIO LAN needs to be "on" 

### 3. USB_Run.py
Run with <sudo ./USB_Run.py>. <RunTime> <TriggerSet> sudo is required due to device permissions in Linux. This option is slower but a more reliable connection. Raspberry pi must be hardwired to USB-B port on back of Rigol scope. use <lsusb> command in Linux shell to check that Pi recognizes scope. 

Utility -> IO Setting -> USB Device should be set to "Computer"


## Important Notes for Use

### What you see is what you get. 
If you try to set the trigger level to a value not displayed on the screen of the scope, it will confuse the scope and disrupt the connection. Likewise if you are collecting a waveform that does not fit on the screen of the scope, the returned data will show an incomplete waveform. 

### Hardware resets sometimes, and that cannot be dealt with through this program. 
Sometimes the scope freezes or will reset, and you may need to be physically present to power cycle the scope in this case, as this type of issue may not be fixed remotely. 

### This is for testing purposes, it is not replacement for fast data acqusition systems.
It takes about a second to get each waveform; getting four waveforms takes four seconds. 

### USB interface and using LXI gives nonfatal error messages 
USB gives an error message at exit that I did not trouble shoot since it does not affect performance. LXI gives a nonfatal error while collecting data. It is annoying but does not really matter as far as I can tell. 

