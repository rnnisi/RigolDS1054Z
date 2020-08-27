#!/usr/bin/env python3
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
"""

import RigolDS1054Z as RS

acqt = input("Enter desired duration of acqusition time in seconds: ") 

rigol = RS.RigolDS1054Z()
rigol.Connect() # establish connection
rigol.SetupNormCollection(1200) # tell scope we want 1200 points in each waveform
rigol.GetParams() # get paramters for generation of x data. do this before DAQ in case of crash
rigol.setupDAQf() # configure output files
rigol.SetAutoTrig() # trigger needs to be in auto mode
rigol.GeneralAuto(float(acqt))  # collect waveforms from screen for acqt
rigol.autogenCSV()  # when acqt is over, or if GeneralAuto encounters a fatal error, generate a CSV for each waveform.
print("Program finished. Exiting...")
