#!/usr/bin/env python3
# Rebecca Nishide, last updated 10/26/2020
# rnnishide@ucsb.edu
#
"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
args[1] = RunTime in seconds
args[2] = lxi, or normal. use LXU for faster data acquisition if lxi is installed
args[3] = trigger level, no spaces, include units V, mV, or uV. (eg. 15.V)
OPTIONAL: args[4-7] = channel assignments 
Can support between 1-4 channels. 
Reads each channel one at at a time before resetting trigger. 
Not simultaneous. MORE CHANNELS = LONGER RUN TIME
"""

import RigolDS1054Z as RS


rigol = RS.RigolDS1054Z()
args = rigol.CmdLinArg(3)
rigol.Connect('auto')
rigol.setupDAQf()
rigol.SetSingTrig()
rigol.Sing2ChanTrigMode(float(args[1]), str(args[2]), str(args[3]))
print("Program finished. Exiting...")
