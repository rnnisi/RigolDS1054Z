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
data_ch = input("Enter the data chanel number (1, 2, 3, or 4): ")
mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")

rigol = RS.RigolDS1054Z()
rigol.Connect('auto')
rigol.SetupSingTrigCollection(1200, "CHAN" + str(data_ch))	# collect 1200 points
rigol.GetParams()	# essential to do before DAQ incase connection is lost
rigol.setupDAQf()
rigol.SetSingTrig()
rigol.ForceSingTrigMode(float(acqt), mode)
rigol.autogenCSV()
print("Program finished. Exiting...")
