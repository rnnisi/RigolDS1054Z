#!/usr/bin/env python3
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
arg 1 should indicate run time in seconds
arg 2 should indicate lxi or normal. lxi will use lxi-tools for faster DAQ. lxi must be properly installed for this feature
arg 3 should be CHAN1, CHAN2, CHAN3, or CHAN4 to specify which channel data is read from 
arg 4 is IP of scope. mkae sure DHCP is enabled on scope. Check IP in Utility -> IO Setting -> Lan Conf.
"""

import RigolDS1054Z as RS
import sys

#acqt = input("Enter desired duration of acqusition time: ") 

rigol = RS.RigolDS1054Z()
args = rigol.CmdLinArg(5)
rigol.Connect(args[4])
rigol.SetupSingTrigCollection(1200, str(args[3]))
rigol.GetParams()
rigol.setupDAQf()
rigol.SetSingTrig()
rigol.ForceSingTrigMode(float(args[1]), str(args[2]))
rigol.autogenCSV()
print("Program finished. Exiting...")
