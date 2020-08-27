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

acqt = input("Enter desired duration of acqusition time: ") 

rigol = RS.RigolDS1054Z()
rigol.Connect()
rigol.SetupSingTrigCollection(1200)	# collect 1200 points
rigol.GetParams()	# essential to do before DAQ incase connection is lost
rigol.setupDAQf()
rigol.SetSingTrig()
rigol.SingTrigMode(float(acqt))
rigol.autogenCSV()
print("Program finished. Exiting...")
