#!/usr/bin/env python3
#
"""
Pull waveforms from Rigol DS1054Z scope
args[1] = RunTime in seconds
args[2] = 'AUTO', 'FORCE_TRIG', or trigger level; no spaces, include units V, mV, or uV. (eg. 15.V)
OPTIONAL: args[2-6] = channel assignments; must be integer between 1 and 4. If not provided, all four channels will be read. 
"""

import RigolDS1000Z as RS

rigol = RS.RigolDS1054Z('USB', 'ONLINE')					# Use class RigolDS1054Z
args = rigol.CmdLinArg(3)					# Dictate minimum number of command line arguements acceptable
rigol.Connect('AutoConnect')				# AutoConnect. This arguement can be changed to scope address for manual connection if desired
rigol.SetupDAQ()							# Establish settings, allow program to identify self contained objects specific to experiment
rigol.StartDAQ(args[1])			# Start data acquisition, allow to run until it has surpassed given RunTime
print("Program finished. Exiting...")
ExpDir = rigol.GetExpDir()
rigol.Exit()
