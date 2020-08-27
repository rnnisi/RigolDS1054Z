#!/usr/bin/env python3
# Rebecca Nishide, 08/26/2020
#

"""
Pull waveforms from internal memory by forcing trigger in single trigger mode
Get waveforms as fast as processing allows
Then generate csv for each sample, put in directory 
Log each run
"""

import RigolDS1054Z as RS

acqt = input("Enter desired duration of acqusition time in seconds: ") 

rigol = RS.RigolDS1054Z()
rigol.Connect() # establish connection
rigol.SetupSingTrigCollection(1200)	# tell scope we want 1200 points for each waveform
rigol.GetParams()	# essential to do before DAQ incase connection is lost; this will be used to make x data
rigol.setupDAQf() # configure output files
rigol.SetSingTrig()  # trigger mode needs to be single trigger
rigol.SingTrigMode(float(acqt))  # collect waveforms during specified time window
rigol.autogenCSV()  # when acqt is over, or if SingTrigMode has a fatal error, generate a CSV for each waveform
print("Program finished. Exiting...")
