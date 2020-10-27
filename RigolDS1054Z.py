import pyvisa
import time
import os
import sys
import subprocess
from threading import Thread
import _thread
import re
from multiprocessing import Process,Pipe

class RigolDS1054Z:
	def __init__(self):
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
	def Connect(self, option):	# look for device, connect, no backend or lxi needed 
		if option == 'auto':
			self.GetHostBase()
		else:
			try:
				self.SCPI_addy = str("TCPIP0::" + str(option) + "::INSTR")
				self.rig = self.rm.open_resource(self.SCPI_addy)
				print("Connected to: ",self.rig.write("*IDN?"))
				return self.rig, self.SCPI_addy
			except:
				print("Unable to Connect. Program exiting.")
				sys.exit(0)
		print("Checking memory for device IP...")
		ConnectMemory = self.ConnectFromMemory()
		if ConnectMemory == True:
			return self.rig, self.SCPI_addy
		else:
			pass
		i = 1
		while i < 255: # check first 255 devices 
			if i == 255:	# exit once this number of IP's have been tried 
				print('Device not found on network.\nCheck that:\n	  Scope is on\n    Scope and raspi are both connected to localhost\n	DHCP is enabled in IO Setting on utility panel of scope\n	 LAN is ON in RemoteIO within IO Setting option of scope')
				sys.exit(0)
			else:
				pass
			try:	# try to connect to each ip
				self.SCPI_addy = "TCPIP0::" + str(self.HostBase) + str(i) + "::INSTR"
				self.rig = self.rm.open_resource(self.SCPI_addy)	# check if connection can be made
				print(self.SCPI_addy)
				CorrectDevice = self.VerifyIDN()
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
		time.sleep(0.05)
		i = 0
		while i <10:
			try:
				self.rig = self.rm.open_resource(self.SCPI_addy)
				print("\nConnection Re-established.")
				i = 11
			except:
				i = i +1
				pass
		if i == 10:
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
	def CmdLinArg(self,req_args):
		self.argv = list(sys.argv)
		num_args = len(self.argv)
		if num_args < req_args:
			print("\nCommand Line self.argv rejected.\nCommand line args must include\n    <executable.py> <RunTime> <lxi/auto> <TrigSetting>\nInteger values 1-4 as additional arguements to specify data channels are optional.\n")
			sys.exit(0)
		else:
			pass
		if self.isNumber(self.argv[1]) == False:
			print("Arg[1] rejected, expected float to dictate RunTime")
			sys.exit()
		else:
			pass
		return self.argv
	def Validate_Nch(self, channels):
		remove_duplicates = set(channels)
		check_vals = []
		for i in remove_duplicates:
			if self.isInteger(i) == True:
				pass
			else:
				print("Channel specification ", i, " rejected.\n	Expected integer value of 1-4.")
			if int(i) > 0 and int(i) < 5:
				check_vals.append(i)
			else:
				print("Channel specification ", i, " rejected.\n	Expected integer value of 1-4.")
		return check_vals
	def Get_Nch(self):
		req_args = len(self.argv)
		self.channel_list = []
		print("Reading from:")
		if len(self.argv) == 4:
			print("    No specifications given, reading all four channels")
			self.channel_list = [str(1), str(2), str(3), str(4)]
			self.num_channels = 4
			return self.channel_list
		else:
			self.num_chan_args = len(self.argv) - 4 # there are four required arguements: script, RunTime, lxi, Trigger
			for i in range(4, 4 + self.num_chan_args):	# read extra arguements that specify channels
				self.channel_list.append(self.argv[i])
		print()
		self.channel_list = self.Validate_Nch(self.channel_list)
		for i in self.channel_list:
			print("    Channel ", i)
		num_channels = len(self.channel_list)
		return self.channel_list.sort()
	def query(self, q):		# send question to scope, scope returns value
		try:
			return self.rig.query(q)
		except:	# no device at address
			print("Unable to send query. Connection broken...")
			self.ReConnect()
	def write(self, cmd):	# send command to scope
		try:
			return self.rig.write(cmd)
		except:
			print("Unable to send command. Connection broken...")
			self.ReConnect()
	def ReadFile(self, infile):
		read = open(infile, 'r')
		lines = read.readlines()
		read.close()
		return(lines)
	def Run(self):
		return self.write(":RUN")
	def Stop(self):
		return self.write(":STOP")
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
		self.rig.write("TRIG:SWE SING")
	def SetNormTrig(self):
		self.write(":TRIG:SWE NORM")
	def SetAutoTrig(self):
		self.write(":TRIG:SWE AUTO")
	def CoupAC(self):
		self.write(":TRIG:COUP AC")
	def CoupDC(self):
		self.write(":TRIG:COUP DC")
	def CoupLFR(self):
		self.write(":TRIG:COUP LFR")
	def CoupHFR(self):
		self.write(":TRIG:COUP HFR")
	def TrigChanEdge(self, trig_ch):
		self.rig.write(":TRIG:MODE EDGE")
		self.rig.write(":TRIG:SWE SING")
		self.rig.write(":TRIG:EDGE:SOUR " + str(trig_ch))		
	def TrigChanRS232(self, trig_ch):
		self.rig.write(":TRIG:MODE RS232")
		self.rig.write(":TRIG:SWE SING")
		self.rig.write(":TRIG:RS232:SOUR " + str(trig_ch))
	def TrigLevRS232(self, level):
		self.rig.write(":TRIG:MODE RS232")
		self.rig.write(":TRIG:RS232:LEV " + str(level))
		self.rig.write(":TRIG:SWE SING")
	def TrigLevEdge(self, level):
		self.rig.write(":TRIG:MODE EDGE")
		self.rig.write(":TRIG:EDG:LEV " + str(level))
		self.rig.write(":TRIG:SWE SING")
	def SetupCollection(self, n, dat_ch):	# use if scope is in auto
		if self.isInteger(dat_ch) == True:
			pass
		else:
			print("Command line arguement not accepted.")
			sys.exit(0)
		try:
			self.rig.timeout = 3000
			self.rig.write(":WAV:MODE NORM")
			self.rig.write("WAV:SOUR CHAN" + str(dat_ch))
			self.rig.write(":WAV:FORM ASC")
			self.rig.write("WAV:STAR 1")
			self.rig.write("wav:STOP "+ str(n))
		except:
			print("Unable to send parameters to scope. Reconnecting")
			self.ReConnect()
	def saveSetup(self):	# use to save configuration 
		q = ":SYST:SET?"
		self.rig.write(q)
		check_len = self.rig.read_bytes(10)
		N = int(check_len[2:len(check_len)])
		self.rig.write(q)
		setup = self.rig.read_bytes(N)
		setup_name = input("Enter name to save configuration under: ")
		f = open("Setups.txt", 'a+')
		f.write('\n\n' + str(time.asctime()) + ', ' + setup_name + ' == ' + str(setup))
		f.close()
	def GetVoltages(self, n, dat_ch):	# get voltages, no lxi
		self.SetupCollection(n, dat_ch)
		q = (":WAV:DATA?\n")		
		self.rig.write(q)
		time.sleep(0.01)
		self.a = []
		i = 0
		self.a = (self.rig.read_bytes(int(n)*12 + int(n)-1))
		return self.a
	def GetParams_Nch(self):	# get params 
		self.xinc = []
		self.xor = []
		for i in self.channel_list:
			try:
				self.rig.write(":WAV: SOUR CHAN" + str(int(i)))
				self.rig.write(":WAV:XINC?")
				time.sleep(0.01)
				self.xinc.append(str(self.rig.read_bytes(12))[1:])
				self.rig.write(":WAV:XOR?")
				time.sleep(0.01)
				self.xor.append(str(self.rig.read_bytes(13))[1:])
			except:
				print("Connection Error.\nAttempting Re-Connection...")
				self.ReConnect()
		self.params.update({'xinc' : self.xinc})
		self.params.update({'xor' : self.xor})
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
		return [self.out, self.exp]	# output file will be returned as a string with name, number, and extension
	def setupDAQf(self):	# establish output files, experiment number for run 
		check = self.checkdir(self.FirstOutFile, self.AssignOutFile)
		self.datf = open(check[0], 'w+')
		self.exp = int(float(check[1]))
		self.TriggerLog = eval(self.TriggerLog)
		self.directory = "Exp_" + str(self.exp)
		self.Get_Nch()
		print("\nData outputting to ", self.directory, '\n')
		return self.exp
	def mkdir(self):
		cmd = 'mkdir ./' + self.directory
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['pwd'], shell = True)
	def readRawDat(self):
		self.datf.close()
		self.rawdat = list(self.ReadFile(self.directory + '.txt'))
	def extractVoltageDat(self, csv_name, i):
		df = open('./' + self.directory + '/' + fn)
		ydat = []
		v = list(str(rawdat[i]).split(','))
		df.write(v[0] + '\n')
		for k in range(1, len(v)):
			if v[k].find('\n') == -1:
				ydat.append(v[k])
			else:
				pass
		return ydat
	def generateTimeDat(self, xinc, length):
		xinc = float(xinc[1:len(xinc) -1])
		xdat = []
		for i in range(1,length -1):
			x = xinc * k
			xdat.append(x)
		return xdat
	def writeCSV(self, csv_name, xdat, ydat):
		csv = open(csv_name, 'w+')
		for i, j in zip(xdat, ydat):
			csv.write(str(xdat[i]) + ', ' + str(ydat[i]) + '\n')
		csv.close()	
	def autogenCSV_Nch(self):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		self.mkdir()
		rawdat = list(self.ReadFile("Exp_" + str(self.exp) + '.txt'))
		xinc = self.params.get('xinc')
		I = 1
		dat_ch_index = 0	# keep a running count of channel index 
		for i in range(len(rawdat)):
			dat_ch = self.channel_list[dat_ch_index]
			XINC = xinc[dat_ch_index]
			df = open('./'+self.directory+'/Wfm_' + str(I) + '_Ch_' + str(dat_ch) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
			df.write(v[0] + '--- XINC: ' + str(XINC) + '\n')
			for k in range(1,len(v)):
				if v[k].find('\n') == -1:
					ydat.append(v[k])
				else:
					pass
			for k in range(len(ydat)):
				x = float(XINC[1:len(XINC)-1]) * k
				df.write(str(x) + ', ' + ydat[k] + '\n')
			df.close()
			if dat_ch_index == self.num_channels - 1:
				print("\nProcessed set #", I)
				I = I + 1
				dat_ch_index = 0 #reset index count 
			else:	
				dat_ch_index = dat_ch_index + 1	# read next channel
				pass
	def writeTriggerLog(self, TriggerStatus):
		trig_log = open(self.TriggerLog, 'w+')
		trig_log.write("Reading Channels: ")
		for i in range(self.num_channels):
			if i < self.num_channels -1:
				trig_log.write(self.channel_list[i] + ', ')
			else:
				trig_log.write(self.channel_list[i] + '\n')
		xinc = self.params.get('xinc')
		xor = self.params.get('xor')
		trig_log.write("Parameters (index matches channel list):")
		for i in range(self.num_channels):
			if i < self.num_channels- 1:
				trig_log.write('xinc = ' + str(xinc[i]) + ' & xor = ' + str(xor[i]) + ', ')
			else:
				trig_log.write('xinc = ' + str(xinc[i]) + ' & xor = ' + str(xor[i]) + '\n')
		for i in range(len(TriggerStatus)):
			trig_log.write(str(i) + ', ' + str(TriggerStatus[i]))
		trig_log.close()
	def TimeOut(self):	# timeout feature to force exit if anything gets stuck due to out of control/external causes
		time.sleep(30)	# set timeout for operations defined in this class
		print("\nData Acq timed out.\nCheck if scope is powered.\nExiting program.")
		self.datf.close()
		_thread.interrupt_main()
		sys.exit(0)
	def WriteOutWv(self, n, child_conn, mode, dat_ch, trig_stat):	# option to use lxi software or self contained capabilities 
		st = time.perf_counter()
		self.datf.write("CHAN" + str(int(dat_ch)) + " --- StartTime: " + str(st) + ' --- TrigStat: ' + str(trig_stat)[:len(str(trig_stat))-2] + ',')
		to = Thread(target = self.TimeOut)
		to.setDaemon(True)	# let timeout run in background. it will interrupt if parent gets stuck.
		to.start()
		try:
			if mode == 'LXI':
				print("\nNOTE: LXI GIVES NONFATAL ERROR. DISREGARD.")
				attempt = 0 
				while attempt < 10:
					try:
						self.SetupCollection(n, dat_ch)
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
				vstr = self.GetVoltages(n, dat_ch)
			vstr = str(vstr)
			volts = vstr[13:len(vstr)-1]	# remove byte characters
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
		except pyvisa.errors.VisaIOError:	# no device at address, the rest of these are non-fixable internally
			print("Error: pyvisa unable to operate")
			try:
				print("Lost contact. Check if scope is powered. System exiting.")
				child_conn.send('NoConn')
				child_conn.close()
				#os._exit(0)
			except TypeError:
				print("Intrument stopped responding.\nExiting Program.")
				child_conn.send('NoConn')
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
	def GeneralAuto(self, acqt, mode, chan_n):	# collects waveforms as fast as it can, no trigger consideration 
		#mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		#notes = input("\nEnter any short notes you wish to log with this experiment: ")
		notes = ''
		self.SetAutoTrig()
		st = time.perf_counter()
		i = 1
		log = open("ExpLog.txt", 'a+')
		while time.perf_counter() - st < float(acqt):
			print("Acquiring waveform #", i)
			try:
				parent_conn, child_conn = Pipe()
				p1 = Process(target = self.WriteOutWv, args = ('1200', child_conn, mode, chan_n, 'AUTO'))
				p1.start()
				stat = parent_conn.recv()
				if stat == 'NoConn':
					print("No Connection...")	# if exit status indicates no more data can be taken, move on to data processing
					p1.join()
					break
				elif stat == 'BrokenPipe':	# get exit status of subprocess, try reconnecting 
					print("Broken Pipe")
					time.sleep(0.01)
					p1.join()
					self.ReConnect()
					time.sleep(0.01)
				else:	# if everything went fine, keep going 
					i = i +1
					p1.join()
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", CHAN" + str(chan_n) + ", Auto Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ", Notes = " + str(notes))
		log.close()
		self.autogenCSV_Nch()
		print("Elapsed Time: ", RunTime)
	def ForceSingTrigMode(self,acqt, mode, chan_n):	
		"""
		forces trigger and collects waveforms during stop mode, resets, as fast as possible
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		st = time.perf_counter()
		i = 0
		log = open("ExpLog.txt", 'a+')
		while time.perf_counter() - st < float(acqt):
			print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				self.write(":TFOR")
				self.Stop()
				parent_conn, child_conn = Pipe()
				p1 = Process(target = self.WriteOutWv, args = ('1200',child_conn, mode, chan_ni, 'FORCE_TRIG'))
				p1.start()
				stat = parent_conn.recv()
				if stat == 'NoConn':
					print("No Connection ...")
					p1.join()
					break
				elif stat == 'BrokenPipe':
					print("Broken Pipe")
					time.sleep(0.01)
					self.ReConnect()
					p1.join()
				else:
					i = i +1
					p1.join()
					try:
						self.ReConnect()
						self.Run()
					except:
						break
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", CHAN" + str(chan_n) + " , Force Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ", " + str(self.params))
		log.close()
		self.autogenCSV_Nch()
		print("Elapsed Time: ", RunTime)
	def SingTrigMode(self,acqt, mode, chan_n, trig_lev):
		"""
		check trigger, get waveform if scope is triggered, reset trigger
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		st = time.perf_counter()
		i = 0
		log = open("ExpLog.txt", 'a+')
		self.SetSingTrig()
		self.TrigLevEdge(trig_lev)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				self.TriggerStatus.append(trig_stat)
				print(type(trig_stat))
				if trig_stat == 'RUN\n':
					pass
				elif trig_stat == 'WAIT\n':
					pass
				else:
					print("Acquiring waveform #", i)
					parent_conn, child_conn = Pipe()
					p1 = Process(target = self.WriteOutWv, args = ('1200',child_conn, mode, chan_n, trig_stat))
					p1.start()
					stat = parent_conn.recv()
					if stat == 'NoConn':
						print("No Connection ...")
						p1.join()
						break
					elif stat == 'BrokenPipe':
						print("Broken Pipe")
						time.sleep(0.01)
						self.ReConnect()
						p1.join()
					else:
						i = i +1
						p1.join()
						try:
							self.Run()
							time.sleep(0.1)
							self.SetSingTrig()
						except:
							break
					#self.SetSingTrig()
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", CHAN" + str(chan_n) + " , Single Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ', '+ str(self.params))
		log.close()
		self.writeTriggerLog(self.TriggerStatus)
		self.autogenCSV_Nch()
		print("Elapsed Time: ", RunTime)
	def Sing4ChanTrigMode(self,acqt, mode, trig_lev):
		"""
		check trigger, get waveform if scope is triggered, reset trigger
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		self.GetParams_Nch(4)
		st = time.perf_counter()
		i = 0	# iteration number
		log = open("ExpLog.txt", 'a+')
		self.SetSingTrig()
		self.TrigLevEdge(trig_lev)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				self.TriggerStatus.append(trig_stat)
				if trig_stat == 'RUN\n':
					pass
				elif trig_stat == 'WAIT\n':
					pass
				else:
					print("Acquiring waveform set #", i)
					print(trig_stat)
					parent_conn, child_conn = Pipe()
					for j in range(1, 5):
						p1 = Process(target = self.WriteOutWv, args = ('1200',child_conn, mode, j, trig_stat))
						p1.start()
						stat = parent_conn.recv()
						if stat == 'NoConn':
							print("No Connection ...")
							p1.join()
							break
						elif stat == 'BrokenPipe':
							print("Broken Pipe")
							time.sleep(0.01)
							self.ReConnect()
							p1.join()
						else:
							#i = i +1
							p1.join()
					try:
						self.Run()
						time.sleep(0.1)
						self.SetSingTrig()
					except:
						break
					#self.SetSingTrig()
				i = i +1
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + " , Single Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ', '+ str(self.params))
		log.close()
		self.writeTriggerLog(self.TriggerStatus)
		self.autogenCSV_Nch()
		print("Elapsed Time: ", RunTime)
	def Sing2ChanTrigMode(self,acqt, mode, trig_lev):
		"""
		check trigger, get waveform if scope is triggered, reset trigger
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		self.GetParams_Nch()
		st = time.perf_counter()
		i = 0	# iteration number
		log = open("ExpLog.txt", 'a+')
		self.SetSingTrig()
		self.TrigLevEdge(trig_lev)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				self.TriggerStatus.append(trig_stat)
				if trig_stat == 'RUN\n':
					pass
				elif trig_stat == 'WAIT\n':
					pass
				else:
					print("Acquiring waveform set #", i)
					parent_conn, child_conn = Pipe()
					for j in self.channel_list:
						p1 = Process(target = self.WriteOutWv, args = ('1200',child_conn, mode, j, trig_stat))
						p1.start()
						stat = parent_conn.recv()
						if stat == 'NoConn':
							print("No Connection ...")
							p1.join()
							break
						elif stat == 'BrokenPipe':
							print("Broken Pipe")
							time.sleep(0.01)
							self.ReConnect()
							p1.join()
						else:
							#i = i +1
							p1.join()
					try:
						self.Run()
						time.sleep(0.1)
						self.SetSingTrig()
					except:
						break
				i = i +1
			except KeyboardInterrupt:
				try:
					sys.exit(0)
				except:
					sys.exit(0)
			finally:
				pass
		RunTime = time.perf_counter() - st
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + " , Single Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i)+ ", DatChannels = " + str(self.channel_list))
		log.close()
		self.autogenCSV_Nch()
		self.writeTriggerLog(self.TriggerStatus)
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + self.directory], shell = True)
		subprocess.check_output(["ls"], shell = True)
		cmd = "mv " + self.TriggerLog + ' ' + self.directory
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['ls'], shell = True)
		print("Elapsed Time: ", RunTime)

