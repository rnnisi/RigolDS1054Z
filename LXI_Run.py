#!/usr/bin/env python3
#

"""
Pull waveforms, as displayed on screen, from scope as fast as allowed
Log experiment
Generate directory with a csv for each waveform grabbed
args[1] = RunTime in seconds
args[2] = 'AUTO', 'FORCE_TRIG', or trigger level; no spaces, include units V, mV, or uV. (eg. 15.V)
OPTIONAL: args[3-6] = channel assignments 
"""

import RigolDS1054Z as RS


rigol = RS.RigolDS1054Z('LXI')					# Use class RigolDS1054Z, set data acqusition to use LXI. only use this if you have LXI installed and operational.
args = rigol.CmdLinArg(3)					# Dictate minimum number of command line arguements acceptable
rigol.Connect('AutoConnect')				# AutoConnect. This arguement can be changed to scope address for manual connection if desired
rigol.SetupDAQ()							# Establish settings, allow program to identify self contained objects specific to experiment
rigol.StartDAQ(args[1])			# Start data acquisition, allow to run until it has surpassed given RunTime
print("Program finished. Exiting...")
rigol.Exit()
