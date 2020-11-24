"""
Last updated 11/18/2020
UCSB Dept. of Physics
Contact: Rebecca Nishide, rnnishide@gmail.com
"""

import pyvisa
import time
import os
import sys
import subprocess
from threading import Thread
import _thread
from multiprocessing import Process,Pipe

class RigolDS1054Z:
	def __init__(self, interface):
		self.interface = interface
		self.rm = pyvisa.ResourceManager("@py")
		self.params = {}
		self.IDN = "RIGOL TECHNOLOGIES,DS1054Z,DS1ZA201104248,00.04.04.SP3"
		self.FirstOutFile = 'Exp_1'
		self.AssignOutFile = "'Exp_' + str(i)"
		self.IPmem = "remember_IP.txt"
		self.TriggerLog = "'Exp_' + str(self.exp) + '_TriggerLog.txt'"
		self.TriggerStatus = []
		try:	# check host address
			ifconfig = str(subprocess.check_output(['ifconfig | grep -e inet\ 192.168'], shell = True))
			self.host = ifconfig[15:26]
		except:		# not connected to ds 
			pass
	def GetHostBase(self):	# get first three figures in host name 
		try:
			print("\nChecking Network Connection...\n")
			print(self.host)
			self.HostBase = self.host[:len(self.host)-1]	# take off the last number in IP
			while True:
				if self.HostBase[len(self.HostBase)-1:] != '.':
					self.HostBase = self.HostBase[len(self.lh)-1]
				else:
					break
		except:		# wireless is turned off, grep returned empty. exit 
			print("No network detected. Please connect to localhost and try again.\nProgram exiting.\n")
			sys.exit(0)
		return self.HostBase
	def ConnectFromMemory(self):
		mem = open(self.IPmem, 'r')
		self.SCPI_addy = str(mem.read())
		mem.close()
		try:
			self.rig = self.rm.open_resource(self.SCPI_addy)
			print("Connected from memory.")
			print("Connected to: ",self.rig.query("*IDN?"))
			return True
		except:
			print("Unable to connect from memory...\nProceed to auto-connect...")		
			return False
	def VerifyIDN(self):
		try:	# if connection is made, check if dev takes SCPI,
			self.idn = self.rig.query("*IDN?")	# check if we can acquire id
			if str(self.idn)[:26] == self.IDN[:26]:		# check manufacturer and type to make sure it is right device
				print("Rigol scope located\n")
			else:
				print("Located and connected to device via LAN, but device is not Rigol Scope.\nWill continue to search network\n")
			return True
		except:
			print("Located and connected to device via LAN, but could not get ID.\nWill continue to search network\n")
			return False
	def USB_Connect(self):
		resources = self.rm.list_resources()
		print(resources)
		for i in resources:
			print(i)
			if i.find("USB") != -1:
				self.USB_addy = i.strip()
				print(self.USB_addy)
			try:
				self.rig = self.rm.open_resource(self.USB_addy)
				CorrectDevice = self.VerifyIDN()
				if CorrectDevice == True:
					return True
				else:
					print("Connected to UCB device, but ID did not match expected Rigol ID.")
			except:
				pass
		return False
	def Connect(self, option):	# look for device, connect, no backend or lxi needed 
		if self.interface == "USB":
			success = self.USB_Connect()
			if success == True:
				print("\n\n\nConnected to ", self.idn, "...")
				return self.rig
			else:
				print("\nWas unable to establish USB connection with Rigol scope.\nExiting...")
				sys.exit()
		else:
			pass
		if option == 'AutoConnect':
			self.GetHostBase()
		else:
			try:		# leave option to give known IP as arguement. Run scripts can be reworked to take advantage of this function.
				self.SCPI_addy = str("TCPIP0::" + str(option) + "::INSTR")
				self.rig = self.rm.open_resource(self.SCPI_addy)
				print("Connected to: ",self.rig.write("*IDN?"))
				return self.rig, self.SCPI_addy
			except:
				print("Unable to Connect. Program exiting.")
				sys.exit(0)
		print("Checking memory for device IP...")
		ConnectMemory = self.ConnectFromMemory()	# Try connecting to last successful adress 
		if ConnectMemory == True:
			return self.rig, self.SCPI_addy
		else:
			pass
		i = 1
		while i < 255: # check first 255 devices 	# Go through IP's on network until connection is accepted
			if i == 255:	# exit once this number of IP's have been tried 
				print('Device not found on network.\nCheck that:\n	  Scope is on\n    Scope and raspi are both connected to localhost\n	DHCP is enabled in IO Setting on utility panel of scope\n	 LAN is ON in RemoteIO within IO Setting option of scope')
				sys.exit(0)
			else:
				pass
			try:	# try to connect to each ip
				self.SCPI_addy = "TCPIP0::" + str(self.HostBase) + str(i) + "::INSTR"
				self.rig = self.rm.open_resource(self.SCPI_addy)	# check if connection can be made
				print(self.SCPI_addy)
				CorrectDevice = self.VerifyIDN()	# Verify that you are connected to the Rigol scope.
				if CorrectDevice == True:
					break
				else:
					i = i +1
			except ConnectionRefusedError:	# device like laptop will refuse connection 
				i = i+1	
			except BrokenPipeError:			# can be due to dev or computer not properly connected to local host 
				i = i+1
			except OSError:
				pass
			except pyvisa.errors.VisaIOError:	# no device at address
				try:
					i = i+1
					pass
				except TypeError:	# workaround 
					i = i+1
					pass	
		print("\nConnected to: ", self.idn + "\n\n\n")
		mem = open(self.IPmem, 'w+')
		print("\nUpdating memory...")
		mem.write(str(self.SCPI_addy))
		mem.close()
		return self.rig
	def ReConnect(self):
		if self.interface == 'USB':
			ReConnCmd = "self.rm.open_resource(self.USB_addy)"
		else:
			ReConnCmd = "self.rm.open_resource(self.SCPI_addy)"
		time.sleep(0.05)
		i = 0
		attempts = 10	# Set number of recconnection attempts to avoid infinite reattempts
		while i < attempts:
			try:
				self.rig = eval(ReConnCmd)
				print("\nConnection Re-established.")
				self.Clear()
				i = 11
			except:
				time.sleep(0.25)
				i = i +1
				print(i)
				pass
		if i == 10:
			try:
				self.Connect()
			except:
				print("    Unable to repair connection. System exiting...")
				sys.exit(0)
	def isInteger(self, test):
		try:
			int(test)
			return True
		except:
			return False
	def isNumber(self, test):
		try:
			float(test)
			return True
		except:
			return False
	def isNoneType(self, test):
		if type(test) == None:
			return True
		else:
			return False
	def isTriggerArg(self, test):	# determine what trigger type is being requested by user
		if test.upper() == 'AUTO':	# remove case sensitivity 
			print("\nTrigger method will be set to auto...")
			return 'AUTO'
		else:
			pass
		if test.upper() == "FORCE":
			print("\nSetting method will be set to force single...")
			return "FORCE"
		else:
			pass
		if test.find('V') != -1:
			print("\nTrigger will be set to ", test, "...")
			self.trig_lev = test
			return "SINGLE"
		else:
			print("Expected command arg[2] to specify trigger setting (auto, force, or voltage value for single trigger method).\narg[2] rejected.\nSystem exiting...\n")
			sys.exit(0)
	def CmdLinArg(self,req_args):	# Check user inputted acceptable command line arguements
		self.argv = list(sys.argv)
		num_args = len(self.argv)
		if num_args < req_args:
			print("\nCommand Line self.argv rejected.\nCommand line args must include\n    <executable.py> <RunTime> <lxi/auto> <TrigSetting>\nInteger values 1-4 as additional arguements to specify data channels are optional.\n")
			sys.exit(0)
		else:
			pass
		if self.isNumber(self.argv[1]) == False:
			print("Expected command arg[1] to be value to specify RunTime.\narg[1] rejected. \nSystem exiting....")
			sys.exit()
		else:
			pass
		return self.argv
	def Validate_Nch(self, channels):	# Clean up data channels requested from user
		remove_duplicates = set(channels)
		check_vals = []
		for i in remove_duplicates:
			if self.isInteger(i) == True:
				if int(i) > 0 and int(i) < 5:
					check_vals.append(i)
				else:			
					print("Channel specification ", i, " rejected.\n	Expected integer value of 1-4.")
			else:
				print("Channel specification ", i, " rejected.\n	Expected integer value of 1-4.")
		return check_vals
	def Get_Nch(self):	# Generate list of channels in ascending order which will be referred to throughout the program
		self.channel_list = []
		if len(self.argv) == 3:
			print("\nNo specifications given, reading all four channels")
			self.channel_list = [str(1), str(2), str(3), str(4)]
			self.num_channels = 4
			return self.channel_list
		else:
			self.num_chan_args = len(self.argv) - 3 # there are four required arguements: script, RunTime, lxi, Trigger
			for i in range(3, 3 + self.num_chan_args):	# read extra arguements that specify channels
				self.channel_list.append(self.argv[i])
		print()
		self.channel_list = self.Validate_Nch(self.channel_list)
		print("Reading from: ")
		for i in self.channel_list:
			print("    Channel ", i)
		self.num_channels = len(self.channel_list)
		return self.channel_list.sort()
	def query(self, q):		# send question to scope; use for SCPI command that prompt scope to send value back 
		try:
			return self.rig.query(q)
		except:	# no device at address
			print("Unable to send query. Connection broken...")
			self.ReConnect()
	def write(self, cmd):	# send command to scope
		i = 0
		while i <6:
			try:
				self.rig.write(cmd)
				i = 6
			except:
				i = i + 1
				print("Unable to send command: ", cmd)
				self.ReConnect()
	def ReadFile(self, infile):	# read infile, return contents list of each line
		read = open(infile, 'r')
		lines = read.readlines()
		read.close()
		return(lines)
	def Run(self):
		return self.write(":RUN; *OPC")
	def Stop(self):
		return self.write(":STOP; *OPC")
	def Clear(self):
		return self.write("*CLS")
	def CheckOPC(self):
		print("check OPC")
		time.sleep(0.1)
		self.query("*OPC?")
		time.sleep(0.02)
		stat = self.rig.read_bytes(1)
		return stat
	def SetOPC(self):
		return self.write("*OPC")
	def Restart(self):
		return self.write("*RST")
	def IDN(self):
		return self.query("*IDN?")
	def TrigStat(self):
		return self.query(":TRIG:STAT?")
	def TrigHoldSet(self, time):
		return self.write(":TRIG:HOLD " + str(time)) 
	def TrigHoldStat(self):
		return self.query(":TRIG:HOLD?")
	def TrifPosStat(self):
		return self.query(":TRIG:POS?")
	def SetSingTrig(self):
		self.write("TRIG:SWE SING")
	def SetNormTrig(self):
		self.write(":TRIG:SWE NORM")
	def SetAutoTrig(self):
		self.write(":TRIG:SWE AUTO")
	def ForceTrig(self):
		self.write(":TFOR")
	def CoupAC(self):
		self.write(":TRIG:COUP AC")
	def CoupDC(self):
		self.write(":TRIG:COUP DC")
	def CoupLFR(self):
		self.write(":TRIG:COUP LFR")
	def CoupHFR(self):
		self.write(":TRIG:COUP HFR")
	def TrigChanEdge(self, trig_ch):
		self.write(":TRIG:MODE EDGE")
		self.write(":TRIG:SWE SING")
		self.write(":TRIG:EDGE:SOUR " + str(trig_ch))		
	def TrigChanRS232(self, trig_ch):
		self.write(":TRIG:MODE RS232")
		self.write(":TRIG:SWE SING")
		self.write(":TRIG:RS232:SOUR " + str(trig_ch))
	def TrigLevRS232(self, level):
		self.write(":TRIG:MODE RS232")
		self.write(":TRIG:RS232:LEV " + str(level))
		self.write(":TRIG:SWE SING")
	def TrigLevEdge(self, level):
		self.write(":TRIG:MODE EDGE")
		self.write(":TRIG:EDG:LEV " + str(level))
		self.write(":TRIG:SWE SING")
	def SetupCollection(self, dat_ch):	# use if scope is in auto
		self.timeout = 3000
		self.Clear()
		self.write(":WAV:MODE NORM")
		self.write("WAV:SOUR CHAN" + str(dat_ch)) 
		self.write(":WAV:FORM ASC")
		self.write(":WAV:STAR 1")
		self.write(":WAV:STOP 1200")
	def ChangeChannel(self, dat_ch):
		self.write(":WAV:SOUR CHAN" + str(dat_ch))
		self.write(":WAV:FORM ASC")
		time.sleep(0.02)
	def saveSetup(self):	# use to save configuration 
		q = ":SYST:SET?"
		self.query(q)
		check_len = self.rig.read_bytes(10)
		N = int(check_len[2:len(check_len)])
		self.rig.write(q)
		setup = self.rig.read_bytes(N)
		setup_name = input("Enter name to save configuration under: ")
		f = open("Setups.txt", 'a+')
		f.write('\n\n' + str(time.asctime()) + ', ' + setup_name + ' == ' + str(setup))
		f.close()
	def GetVoltages(self, dat_ch):	# get voltages, no lxi
		self.ChangeChannel(dat_ch)
		if self.interface == 'LAN' or self.interface == 'LXI':	# LAN and USB recieve data packets differently
			N = 1200*12 + 1200-1
		else:
			N = 1
		q = (":WAV:DATA?")		
		self.write(q)
		time.sleep(0.1)
		while True:
			try:
				self.a = self.rig.read_bytes(N)
				break
			except pyvisa.errors.VisaIOError:	# no device at address, the rest of these are non-fixable internally
				time.sleep(0.1)
				self.write(q)
				print("Error: pyvisa unable to operate")
				try:
					print("Could not read voltages. Re-attempting.")
				except TypeError:
					print("Cound not read voltages. Re-attempting.")
		return self.a
	def GetParam(self, cmd):	# collect specified parameter
		if self.interface == 'USB':
			self.write("WAV:" + cmd + "; *OPC")
			param = self.rig.read_bytes(1).decode('utf-8')
		else:
			self.write("WAV:" + cmd)
			time.sleep(0.02)	
			param = ''
			while True:
				try:
					chunk = (self.rig.read_bytes(1)).decode('utf-8')
				except:
					pass
				if chunk != '\n':
					param = param + chunk
				else:
					break
		if self.isNoneType(param) == False:
			return param.strip()
		else:
			print("Failed to get param", cmd)
	def GetParams_Nch(self):	# get parameters from scope for reference to in program and later reference
		print("\nGetting scope parameters...")
		self.xinc = self.GetParam("XINC?\n")
		self.xor = self.GetParam("XOR?\n")
		self.xref = self.GetParam("XREF?\n")
		self.yinc= self.GetParam("YINC?")
		self.yor = self.GetParam("YOR?")
		self.yref = self.GetParam("YREF?")
		self.params.update({'xinc' : self.xinc})	# store data in dictionary
		self.params.update({'xor' : self.xor})		# if you are changing paramters in experiment you can
		self.params.update({'xref' : self.xref})	# alter or write in function to update parameters and index over time
		self.params.update({'yinc' : self.yinc})
		self.params.update({'yor' : self.yor})
		self.params.update({'yref' : self.yref})
		print("    Done!")
		return self.params
	def checkdir(self, f, ff):	# check names of files with name f, number output files to avoid overwriting
		i = 2				# format for f should be : NAME_n.txt with n = 1, 2, 3.....
		if os.path.exists(f) == False:
			self.out = str(f) + '.txt'
			self.exp = 1
			return [self.out, self.exp]
		else:
			while os.path.isdir(f) == True:
				f = eval(ff)
				i = i+1
				os.path.isdir(f)
		self.out = str(f) + '.txt'
		self.exp = str(i - 1)
		return [self.out, self.exp]	# Program will use sequential file labels to keep data indexed and organized within workign directory.
	def mkdir(self):	# make directory for the experiment 
		cmd = 'mkdir ./' + self.directory
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['pwd'], shell = True)
	def writeCSV(self, csv_name, xdat, ydat):
		csv = open(csv_name, 'w+')
		for i, j in zip(xdat, ydat):
			csv.write(str(xdat[i]) + ', ' + str(ydat[i]) + '\n')
		csv.close()	
	def autogenCSV_Nch(self, exp):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		self.mkdir()
		rawdat = list(self.ReadFile("Exp_" + str(exp) + '.txt'))
		I = 1
		dat_ch_index = 0	# keep a running count of channel index 
		for i in range(len(rawdat)):
			dat_ch = self.channel_list[dat_ch_index]
			df = open('./'+self.directory+'/Wfm_' + str(I) + '_Ch_' + str(dat_ch) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
			df.write(v[0] + '--- XINC: ' + str(self.xinc) + '\n')
			df.write("Time (seconds), Voltages (V)\n")
			for k in range(1,len(v)):
				if v[k].find('\n') == -1:
					ydat.append(v[k])
				else:
					pass
			for k in range(len(ydat)):
				x = float(self.xinc) * k
				df.write(str(x) + ', ' + ydat[k] + '\n')
			df.close()
			if dat_ch_index == self.num_channels - 1:
				print("\nProcessed set #", I)
				I = I + 1
				dat_ch_index = 0 #reset index count 
			else:	
				dat_ch_index = dat_ch_index + 1	# read next channel
				pass
	def writeTriggerLog(self, TriggerStatus, StartTime):	# record each time and trigger, may be useful for later signal processing
		trig_log = open(self.TriggerLog, 'w+')		# will keep track of parameters, time, program and scope settings to automate good experimental practices
		trig_log.write("Reading Channels: ")
		for i in range(self.num_channels):
			if i < self.num_channels -1:
				trig_log.write(self.channel_list[i] + ', ')
			else:
				trig_log.write(self.channel_list[i] + '\n')
		trig_log.write("Parameters(xinc, xor, xref, yinc, yor, yref): \n")
		trig_log.write("	" + self.xinc + ", " + self.xor + ', ' + self.xref + ', ' + self.yinc + ',' + self.yor + ', ' + self.yref + '\n')
		trig_log.write("Trigger: " + str(self.trig_lev) + '\n')
		trig_log.write("Interface: " + self.interface + '\n')
		trig_log.write('---\n')
		if TriggerStatus != 'NA':
			for i in range(1, len(TriggerStatus)):
				trig_log.write(str(i) + ', ' + str(TriggerStatus[i]) + '\n')
		else:
			pass
		trig_log.close()
	def TimeOut(self):	# timeout feature to force exit if anything gets stuck due to out of control/external causes
		time.sleep(30)	# set timeout for operations defined in this class
		print("\nData Acq timed out.\nCheck if scope is powered.\nExiting program.")
		self.datf.close()
		_thread.interrupt_main()
		sys.exit(0)
	def WriteOutWv(self, n, child_conn, dat_ch, trig_stat):	# option to use lxi software or self contained capabilities 
		st = time.perf_counter()
		self.datf.write("CHAN" + str(int(dat_ch)) + " --- StartTime: " + str(st) + ' --- TrigStat: ' + str(trig_stat)[:len(str(trig_stat))-2] + ',')
		to = Thread(target = self.TimeOut)
		to.setDaemon(True)	# let timeout run in background. it will interrupt if parent gets stuck.
		to.start()
		try:
			if self.interface == 'LXI':
				print("\nNOTE: LXI GIVES NONFATAL ERROR. DISREGARD.")
				attempt = 0 
				while attempt < 10:
					try:
						self.SetupCollection(dat_ch)
						vstr = subprocess.check_output(['lxi scpi --address ' + str(self.SCPI_addy)[8:19] + ' ":WAV:DATA?"'], shell = True)
						attempt = 11
					except:
						pass
						attempt = attempt + 1
				if attempt == 10:
					print("Failed to Connect...\n")
					self.datf.close()
					child_conn.send('NoConn')
					child_conn.close()
					os._exit(0)
				else:
					pass
			else:
				vstr = self.GetVoltages(dat_ch)
			vstr = str(vstr)
			volts = vstr[13:len(vstr)-1]	# remove header and byte characters
			self.datf.write(str(volts) + '\n')
			rt = time.perf_counter() - st
			child_conn.send('cont')	# went ok 
			child_conn.close()
			os._exit(0)
		except KeyboardInterrupt:
			self.datf.close()
			sys.exit(0)		# exit
		except ConnectionResetError:
			print("Device disconnected")
			child_conn.send('BrokenPipe')	# let program know pipe is down, fixable problem 
			child_conn.close()
			os._exit(0)
		except BrokenPipeError:
			child_conn.send('BrokenPipe')	# let program know pipe is down, this is fixable
			child_conn.close()
			os._exit(0)
		except subprocess.CalledProcessError:
			try:
				child_conn.send('NoConn')
				child_conn.close()
				os._exit(0)
			except TypeError:
				print("Instrument reset, acquisiton failed.")
				child_conn.send('NoConn')
				child_conn.close()
				os._exit(0)
	def GetWaveformSet(self, trig_stat):	# use multiprocessing to gather waveform
		parent_conn, child_conn = Pipe()
		for j in self.channel_list:
			print("    Channel ", j, " data acquired...")
			p1 = Process(target = self.WriteOutWv, args = ('1200',child_conn, j, trig_stat))
			p1.start()
			stat = parent_conn.recv()
			if stat == 'NoConn':
				print("No Connection ...")
				p1.join()
				return "fail"
			elif stat == 'BrokenPipe':
				print("Broken Pipe")
				time.sleep(0.01)
				self.ReConnect()
				p1.join()
				operation = "pipe fix"
			else:
				p1.join()
				operation =  "success"
		return operation
	def WriteExpLog(self, RunTime, i):	# Record experiment
		log = open("ExpLog.txt", 'a+')
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", Interface = " + str(self.interface) + ", ChannelList = " + str(self.channel_list) + ", Trigger = " + self.TriggerMode + ", AcqTime = " + str(RunTime) + ", ScopeChecks = " + str(i))
		log.close()
	def CallParams(self):	 # call function to get parameters
		self.Run()	# error handling written in in case scope is overwhelmed
		j = 0
		while j < 11:
			try:
				self.GetParams_Nch()
				j = 12
			except:
				j = j + 1
				self.ForceTrig()
				time.sleep(0.01)
		self.Run()
		time.sleep(0.01)
	def AutoMode(self, acqt):	# collects waveforms as fast as it can on auto, no trigger consideration 
		self.SetAutoTrig()
		st = time.perf_counter()
		i = 1
		self.trig_lev = 'AUTO'
		time.sleep(0.01)
		while time.perf_counter() - st < float(acqt):
			print("\nAcquiring waveform #", i)
			try:
				operation = self.GetWaveformSet('AUTO')
				if operation == "fail":
					print("Lost contact with scope...")
					break
				else:
					i = i + 1
					pass
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		self.WriteExpLog(RunTime, i)
		self.TriggerStatus = 'NA'
		self.writeTriggerLog(self.TriggerStatus, st)
		self.autogenCSV_Nch(self.exp)
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + self.directory], shell = True)
		subprocess.check_output(["ls"], shell = True)
		cmd = "mv " + self.TriggerLog + ' ' + self.directory
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['ls'], shell = True)
		print("Elapsed Time: ", RunTime)
	def ForceTriggerMode(self,acqt):	# force trigger for each check 
		st = time.perf_counter()
		i = 0
		self.trig_lev = 'Force'
		while time.perf_counter() - st < float(acqt):
			print("\nAcquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				self.ForceTrig()
				self.Stop()
				operation = self.GetWaveformSet('FORCE')
				print(operation)
				if operation == "fail":
					break
				else:
					i = i + 1
					pass
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		self.autogenCSV_Nch(self.exp)
		self.WriteExpLog(RunTime, i)
		self.TriggerStatus = 'NA'
		self.writeTriggerLog(self.TriggerStatus, st)
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + self.directory], shell = True)
		subprocess.check_output(["ls"], shell = True)
		cmd = "mv " + self.TriggerLog + ' ' + self.directory
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['ls'], shell = True)
		print("Elapsed Time: ", RunTime)
	def SingleTriggerMode(self, acqt):	# Set single trigger value (set by RN as edge type trigger), collect waveform when triggered
		st = time.perf_counter()	# when not triggered and collecting waveform, keep checking trigger
		i = 0	# iteration number
		self.SetSingTrig()
		self.TrigLevEdge(self.trig_lev)	# change this if you want a type of trigger other than edge
		time.sleep(0.01)
		self.Run()
		time.sleep(0.01)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				try:
					trig_stat = self.TrigStat()
				except:
					print("failed to get status")
					self.ReConnect()
				finally:
					self.TriggerStatus.append(str(trig_stat.strip()) + ", " + str(time.perf_counter()))
				if trig_stat == 'RUN\n' or trig_stat =='WAIT\n' or trig_stat == 'AUTO\n':
					self.Clear()	# ping scope, clear to keep connection open
					pass
				else:
					print("\nAcquiring waveform set #", i)
					operation = self.GetWaveformSet(str(trig_stat).strip())
					if operation == "fail":
						break
					else:
						i = i +1
						pass
					try:
						self.Run()
						time.sleep(0.1)
						self.SetSingTrig()
					except:
						break
			except KeyboardInterrupt:
				break
			finally:
				pass
		RunTime = time.perf_counter() - st
		self.WriteExpLog(RunTime, i)
		self.autogenCSV_Nch(self.exp)
		self.writeTriggerLog(self.TriggerStatus, st)
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + self.directory], shell = True)
		subprocess.check_output(["ls"], shell = True)
		cmd = "mv " + self.TriggerLog + ' ' + self.directory
		subprocess.Popen([cmd], shell = True)
		#subprocess.check_output(['pwd'], shell = True)
		print("Elapsed Time: ", RunTime)
		self.writeTriggerLog(self.TriggerStatus, st)
	def SetupDAQ(self): # Call all the functions we need to set up data acqusition, configure program for experiment
		self.TriggerMode = self.isTriggerArg(self.argv[2])
		outfile = self.checkdir(self.FirstOutFile, self.AssignOutFile)
		self.datf = open(outfile[0], 'w+')
		self.exp = int(float(outfile[1]))
		self.TriggerLog = eval(self.TriggerLog)
		self.directory = "Exp_" + str(self.exp)
		print("\nData in:", self.directory.strip(), '\n')
		self.Get_Nch()
		self.SetupCollection(1)
	def StartDAQ(self, acqt):	# check what kind of data collection is desired, start data collection 
		if self.TriggerMode =='AUTO':
			self.Run()
			self.SetAutoTrig()
			self.CallParams()
			print("\nStarting auto trigger mode data acquisition...\n")
			self.AutoMode(acqt)
		elif self.TriggerMode == 'FORCE':
			self.Run()
			self.ForceTrig()
			self.CallParams()
			print("\nStarting force trigger mode data acquisition...\n")
			self.ForceTriggerMode(acqt)
		else:
			time.sleep(0.05)
			self.CallParams()
			print("\nStarting single trigger mode data acqusition...\n")
			self.SingleTriggerMode(acqt)
	def Exit(self):
		sys.exit(0)
	def GetExpDir(self)
		return "./Exp_" + str(self.esp)
