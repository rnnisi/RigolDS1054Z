#!/usr/bin/env python3
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
"""

import RigolDS1054Z as RS

acqt = input("Enter desired duration of acqusition time: ") 

rigol = RS.RigolDS1054Z()
rigol.Connect()
rigol.SetupNormCollection(1200)
rigol.GetParams()
rigol.setupDAQf()
rigol.GeneralAuto(float(acqt))
rigol.autogenCSV()
print("Program finished. Exiting...")
