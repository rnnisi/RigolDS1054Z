#!/usr/bin/env python3
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
"""

import RigolDS1054Z as RS

acqt = input("Enter desired duration of acqusition time: ") 
data_ch = input("Enter the data chanel number (1, 2, 3, or 4): ")
mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")

rigol = RS.RigolDS1054Z()
rigol.Connect()
rigol.SetupNormCollection(1200, 'CHAN'+str(data_ch))
rigol.GetParams()
rigol.setupDAQf()
rigol.GeneralAuto(float(acqt), mode)
rigol.autogenCSV()
print("Program finished. Exiting...")
