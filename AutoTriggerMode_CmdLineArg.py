#!/usr/bin/env python3
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
arg 1 should indicate run time in seconds
art 2 should indicate lxi or normal. lxi will use lxi-tools for faster DAQ. lxi must be properly installed for this feature
"""

import RigolDS1054Z as RS
import sys

#acqt = input("Enter desired duration of acqusition time: ") 

rigol = RS.RigolDS1054Z(3)
args = rigol.CmdLinArg('auto')
rigol.Connect()
rigol.SetupNormCollection(1200)
rigol.GetParams()
rigol.setupDAQf()
rigol.GeneralAuto(float(args[1]), str(args[2]))
rigol.autogenCSV()
print("Program finished. Exiting...")
