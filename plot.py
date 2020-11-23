#!/usr/bin/env python3
#

import matplotlib.pyplot as plt
import numpy
import sys
import subprocess

args = sys.argv

exp = args[1]

# open log to get channel info 
TriggerLog = subprocess.check_output(['ls *TriggerLog.txt'], shell = True)
trig_file = TriggerLog.decode("utf-8")
trig_file = trig_file.strip()
trig_log = open(trig_file, 'r')
lines = trig_log.readlines()
trig_log.close()
raw_chan = lines[0].split(':')

# clean up channel numbers 

list_channels = list(raw_chan[1].split(','))
for i in range(len(list_channels)):
	list_channels[i] = list_channels[i].strip()

# read waveforms and store data 
df = "'Wfm_' + str(exp) + '_Ch_' + str(i) + '.csv'"

for i in list_channels:
	try:
		dat = open(eval(df), 'r')
	except FileNotFoundError:
		pass
	raw = str(dat.read())
	lines = list(raw.split('\n'))
	time = []
	volts = []
	for j in range(2, len(lines)):
		try:
			temp = str(lines[j]).split(', ')
			volts.append(float(temp[1]))
			time.append(float(temp[0]))
		except:
			pass
# plot data 
	plt.plot(time, volts, label = "channel " + str(i))


plt.legend()
plt.title("Waveform Set #" + str(exp))
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.show()
