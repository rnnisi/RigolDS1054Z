# RigolDS1054Z


## Purpose
Pull waveforms from scope using python with no backend or driver, over localhost. Program can be used with basic knowledge of how it works, so that researchers may pull waveforms from an oscilloscope as a means of data acqusition. Program is meant to be setup and left alone; changing settings during run may mess with the accuracy of returned data (particularly the timesteps). 

If the OS has lxi-tools and the appropriate peripherals installed, user can take advantage and automate use of lxi-tools to get waveforms using this program and built in error handling. This is faster than using the pyvisa method. Use of lxi-tools is optional. 

get_RigolDS1054Z will automatically check the OS and install requirements. It will make a new directory which contains the contents of this repo. It is mostly for my use, since it is a linux/mac executable which I may give out for easy installation. It requires a deploy key from user, which user must get from me. 

## Program Modes
### 1.	Auto
  a.	Collect waveform data in autotrigger mode as it appears on screen\
  b.	LXI or self options for data acquisition (LXI is faster but requires lxi-tools)\
  c.	Auto-generated directory for experiment with CSV files for each wave form
### 2.	Single Trigger
  a.	Forces trigger, gets waveform, resets\
  b.	LXI or self options for data acquisition (LXI is faster but requires lxi-tools) 

## Program Configuration and Requirements
This program is meant to be run on a Linux OS. It was developed specifically for a raspberry pi. 
Make sure scope is powerd on, and connected to localhost. Computer also needs to be connected to localhost.

On the scope, Utility -> LAN Config -> Configure needs to be on DHCP and Auto, so that IP adress indicates localhost.
Utility -> LAN Config -> RemoteIO LAN needs to be "on" 

### Python Libraries 
- pyvisa
- time
- os
- sys
- subprocess
- threading
- _thread
- re
- multiprocessing

### Optional software
- lxi-tools (requires API and peripheral software, see https://lxi-tools.github.io/) 

## Contents
### RigolDS1054Z.py
library for DAQ from scope. Will work with similar Rigol scopes
### SingleTriggerMode.py
Automates running experiment in Single Trigger mode where trigger is forced and scope is stopped before taking waveform. Program starts by taking user input for DAQ time, whether lxi or pyvisa is used for data acqusition, and asking for any notes for experimental log. Ends by generating CSV's and putting them in directory  labeled by experiment number. 
### SingleTriggerMode.py
Automates running experiment in Auto Trigger mode where waveforms are grabbed from screen. Program starts by taking user input for DAQ time, whether lxi or pyvisa is used for data acqusition, and asking for any notes for experimental log. Ends by generating CSV's and putting them in directory  labeled by experiment number.

## Structure of class: RigolDS1054Z

**Connect(self, option)**:Check the wireless connectivity. 
- option will specify auto, or its value will be the IP of the device. If option is 'auto', then the program will proceed to find the device on the network and connect as described. If not auto, the program will try to connect to the specified IP. IP should be used as an arguement (eg. not 'auto' mode) if user is encountering trouble trying to connect to the device.
- Next will check previously used adress, embedded in memory file. The address for the last sucessful connection is stored in the memory file.
-	If unable to connect from memory, auto mode will the IP of pi and use first three values, changing fourth number (device number), and parse thru values up to 255 to find device. It takes a long time to get to xxx.xxx.x.255, but in practice the scope will generally be assigned a lower digit, since we are using a local host. 
-	Try connecting to each device. If the device rejects the connection, there is no device found, or a connection is made but the ID number of the device does not belong to a Rigol DS1000Z scope, the program will keep searching until it hits xxx.xxx.x.255, at which point the program will exit with the advice to check network connectivity. error messages will be printed when the program runs into the described issues.
- Prints messages to update user what the program is doing, when it is connected, and full id number of scope once connected. 

**ReConnect(self)** : reconnect w device that has already been located by connect

**CmdLinArg(self, n_args)**: take command line arguements. Does not have to be used, but can be used to define arguements for the functions called in the rest of the script. Use user input at beggining to get arguements if not using command line arguements. 
- this function takes the number of arguements expected and checks that the user gave the right number of arguements. Program will kill the process if the right number of arguements are not given.
- Arg 0 is always the python script. 
- Arg 1 is alwasy the acqusitiont time. This function will check that Arg 1 is a floatable value, and kill the process if it is not
- Arg 2 is always 'LXI' or 'normal' to specify if lxi-tools should be used to collect values, or if normal if the internally contained pyvisa method will be used. 
- Arg 3 is always the channel which data will be read from. 
- Arg 4 and up is optionally the IP address of the scope, the trigger level, or the channel which will set the trigger, depending on needs. Check which program is being run. 

**query(self, q)**: send a query to device, has built in error handling

**ReadFile(self, infile)**: read lines of file
- Use to return contents of file as list, one item per line. 

**Run(self)**: tell device to run
**Stop(self)**: tell device to stop 

**IDN(self)**: Get idn of device 

**rigStat(self)**: Get status of trigger
-	Returns: RUN, STOP, AUTO, WAIT, or TD (triggered) 

**TrigHoldSet(self, time)**: Set trigger to hold for time after being triggered

**TrigHoldStat(self)**: Check trigger hold time

**TrigPosStat(self)**: Check trigger position

**findPiIP(self)**: return IP of raspberry pi in case this is useful 

**SetTrigMode(self)**: get user input to set trigger mode. 
-	Contains dictionary so that user can input option, program will convert to SCPI 
-	Trigger types available are outlined on pg 5-8 of Rigol User manual.
-	Edge Trigger
-	Pulse Trigger
-	Slope Trigger
-	Video Trigger
-	Pattern Trigger
-	Duration Trigger
-	Setup/Hold Trigger (Option)
-	TimeOut Trigger (Option)
-	Runt Trigger (Option)
-	Windows Trigger (Option)
-	Delay Trigger (Option)
-	Nth Edge Trigger (Option)
-	RS232 Trigger (Option)
-	I2C Trigger (Option) 
-	SPI Trigger (Option) SetTrigSweep(self): get user input to set trigger sweep.

**SetTrigSweep(self)** user input for Auto, normal, and single 
-	See pg 5-3 in user manual for details on these trigger modes 

**SetSingTrig(self)**: Change trigger to single mode

**SetNormTrig(self)**: Change trigger to normal mode

**SetAutoTrig(self)**: Change trigger to auto mode

**CoupAC(self)**: Couple scope to AC signal 

**CoupDC(self)**: Couple scope to DC signal

**CoupLFR(self)**: Low frequency reject coupling 

**CoupHFR(self)**: high frequency reject coupling 

**TrigChanRS232(self, trig_ch)**: set RS232 mode triggering, make trig_ch trigger source

**TrigChanEdge(self, trig_ch)**: set edge mode triggering, make trig_ch trigger source

**TrigLevRS232(self, level)**: set RS232 mode triggering, set trigger level

**TrigLevEdge(self, level)**: set edge mode triggering, set trigger level

**SetupNormCollection(self, n)**: Send waveform acquisition specifiers to scope 
-	Asks for n points starting from origin to n
-	Specifies format of data output and which chanel to readout from 
-	Normal mode acquisition 

**SetupSingTrigCollection(self, n)**: Send waveform acquisition specifiers to scope 
-	Asks for n points starting from origin to n
-	Specifies format of data output and which chanel to readout from 
-	Normal mode acquisition to read from internal memory while scope is stopped

**GetVoltages(self, n)**: read out specified number of bytes provided by scope upon request of waveform in ASC format 
-	Returns a one-line of ASC voltage values in scientific notation in byte format, which is converted to string type for convenience. Will return specified number of characters based on formula 

**GetParams(self)**: Get scope display parameters
-  Returns dictionary of parameters with keys that make sense, so that user input can easily retrieve the desired values. 
-	Xinc and Xor are especially important here, as the request for waveform returns only voltage values. User needs these parameters to generate the x-axis

**CheckDir(self, f, ff)**: checks working directory for directory, and then generates name for output file with ascending number tags so that data is never overwritten. 
-	f is first directory name, Exp_1
-	ff is the string which will be evaluated to generate the following file names, Exp_n where n = 1, 2, 3...
-	f and ff are defined in __init__(self).

**TimeOut(self)**:
-	to be used in daemon thread to override a process if it is taking too long (eg something is wrong
-	prints error message 
-	this timeout is separate from the one that is set for communication with the scope. It is a timeout for the python processes on the frontend. 

**SetupDAQf(self, n)**: establish writeout file 
-	uses self objects so that file can be manupulaited in various functions 

**WriteOutWv(self, n, mode)**: Get voltage values and record time, and write that out to one data file
-	Takes mode as argument, if mode is LXI, will use LXI to get waveforms. This is a little faster
-	Voltages readout in one line of byte looking characters. Output waveform file (WFM_n.txt)has all the readouts from the run; one line contains an entire waveform. 
-	referes to checkDir to properly number output files
-	referes to getVoltages to acquire waveforms
-	if scope becomes disconnected, collection pauses and tries to reconnect. Program exits if reconnect is not possible. 
-	Uses daemon thread to refer to TimeOut; if scope stops responding (eg. Scope powered down or network is out), the program will save data files and exit.
-	Mean to be used in multiprocessing environment; will send error messages thru pipe to parent process
-	Each waveform dataset is headed by the time at which the acquisition started, and the channel data is from 

**makeCSV(self)**: make waveform csv’s 
-	Put all csv’s in one subdirectory labeled with the experiment number 
-	Generate csv for every waveform with time in first column (seconds), voltage in second (V)
- move raw text file to experiment directory 

**GeneralAuto(self, acqt, mode, chan_n)**: Acquire data 
-	mode allows user to dictate if they want to use LXI or not
- read from chan_n
-	Acquire data as fast as possible for acquisition time with autotrig
-	Establish multiprocess environment to smooth acquisition process and improve error handling.
- In case of loss of connection, program will try to reestablish connection. If impossible, it will save data and continue to processing

**ForceSingTrigMode(self, acqt, mode, chan_n, trig_lev)**: Acquire data by forcing trigger in single trigger mode
-	mode allows user to dictate if they want to use LXI or not
- read from chan_n
-	Acquire data as fast as possible for acquisition time by forcing trigger, reading data, then resetting trigger
-	Establish multiprocess environment to smooth acquisition process and improve error handling. 
- outputs raw data file with waves in byte formats
 
**SingTrigMode(self, acqt, mode, chan_n, trig_lev)** Acquire data when trigger check does not return 'RUN' in single mode (eg when scope is not triggered). Reset single trigger mode after acquiring waveform. 
-	mode allows user to dictate if they want to use LXI or not
- read from chan_n
- set trigger level to trig_lev (in volts)
-	Acquire data as fast as possible for acquisition time by forcing trigger, reading data, then resetting trigger
-	Establish multiprocess environment to smooth acquisition process and improve error handling. 
- outputs raw data file with waves in byte formats
 
## Output Types
### 1.	Waveform file: Wfm_N.txt
-  Each line is one long string of all the voltage readouts.
    This is a string of bytes returned by the scope. Headed by timestamp. This is raw data and needs to be processed to be particularly useful.
-  One per experiment
### 2.	Experiment log: ExpLog.txt
-  Each experiment is automatically logged with number, date/time, acqusition mode, trigger mode, number of waveforms, and user notes.
-  input option for user notes is stored in ExpLog.txt
-  One per Experiment
### 3.	Experiment Directory: ./Exp_n
-  Contains a csv for each waveform, generated from the raw data waveform file. 
### 4. Waveform CSV: Wfm_n.csv
-  CSV has timesteps generated by INITIAL Xdivs. Do not change settings during run; this will cause timesteps to be innacurate
-  First line is start time
-  First column is time on x-axis of scope in seconds, second column is corresponding voltage readouts in volts.

