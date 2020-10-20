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
		#self.dat = "Wfm_1.txt"
		#self.acq = "AcqTimes_1.csv"
		#self.datff = "'Wfm_' + str(i) + '.txt'"
		#self.acqff = "'AcqTimes_' + str(i) + '.csv'"
		self.f = 'Exp_1'
		self.ff = "'Exp_' + str(i)"
		self.IPmem = "remember_IP.txt"
		try:
			ifconfig = str(subprocess.check_output(['ifconfig | grep -e inet\ 192.168'], shell = True))
			self.host = ifconfig[15:26]
		except:		# not connected to ds 
			pass
		try:
			print("\nChecking Network Connection...\n")
			self.lh = self.host[:len(self.host)-1]	# take off the last number in IP
			while True:
				if self.lh[len(self.lh)-1:] != '.':
					self.lh = self.lh[len(self.lh)-1]
				else:
					break
			
		except:		# wireless is turned off, grep returned empty. exit 
			print("No network detected. Please connect to localhost and try again.\nProgram exiting.\n")
			sys.exit(0)
	def Connect(self, option):	# look for device, connect, no backend or lxi needed 
		if option == 'auto':
			pass
		else:
			try:
				self.va = str("TCPIP0::" + str(option) + "::INSTR")
				self.rig = self.rm.open_resource(self.va)
				print("Connected to: ",self.rig.write("*IDN?"))
				return self.rig, self.va
			except:
				print("Unable to Connect. Program exiting.")
				sys.exit(0)
		print("Checking memory for device IP...")
		mem = open(self.IPmem, 'r')
		self.va = str(mem.read())
		mem.close()
		try:
				self.rig = self.rm.open_resource(self.va)
				print("Connected from memory.")
				print("Connected to: ",self.rig.query("*IDN?"))
				return self.rig, self.va
		except:
			pass
		i = 1
		print("Could not connect from memory. Locating device...")
		while i < 255: # check first 255 devices 
			if i == 255:	# exit once this number of IP's have been tried 
				print('''
Device not found on network.
Check that:
  Scope is on
  Scope and raspi are both connected to localhost ds
  DHCP is enabled in IO Setting on utility panel of scope
  LAN is ON in RemoteIO within IO Setting option of scope
''')
				sys.exit(0)
			else:
				pass
			#if == 50:
			#	print("\nChecked first 50 devices. Will continue to 255...")
			#else:
			#	pass
			try:	# try to connect to each ip
				self.va = "TCPIP0::" + str(self.lh) + str(i) + "::INSTR"
				self.rig = self.rm.open_resource(self.va)	# check if connection can be made
				try:	# if connection is made, check if dev takes SCPI, 
					self.idn = self.rig.query("*IDN?")	# check if we can acquire id
					if str(self.idn)[:26] == self.IDN[:26]:		# check manufacturer and type to make sure it is right device
						print("Rigol scope located\n")
						i = 0
						#return self.va
						break	# exit loop iff connection is made, scope is right type
					else:
						print("Located and connected to device via LAN, but device is not Rigol Scope.\nWill continue to search network\n")
						i = i+1	# keep checking devices to find right scope. 
						pass	# in case there are other SCPI enabled devices on local host
				except:
					print("Located and connected to device via LAN, but could not get ID.\nWill continue to search network\n")
					i = i +1
					pass
			except ConnectionRefusedError:	# device like laptop will refuse connection 
				i = i+1	
				pass
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
		print("self.va", self.va)
		mem.write(str(self.va))
		mem.close()
		return self.rig
	def ReConnect(self):
		time.sleep(0.05)
		i = 0
		while i <10:
			try:
				self.rig = self.rm.open_resource(self.va)
				print("\nConnection Re-established.")
				i = 11
			except:
				i = i +1
				pass
		if i == 10:
			print("Unable to fix connection. System exiting...")
			sys.exit(0)
	def CmdLinArg(self,n_args):
		args = list(sys.argv)
		if len(args) != n_args:
			print("""
Command Line Args rejected.
Program Requires different number of arguements.
	arg[1] = RunTime
	arg[2] = lxi or normal 
	arg[3] = n, where n indicates read data from Channel #n
	arg[4] = Trigger level (if applicable), as numerical value followed by units (V, mV, uV)with no spaces 
	arg[5] = IP  (if applicable)
			""")
			sys.exit(0)
		else:
			pass
		try:
			float(args[1])
		except ValueError:
			print("Command Line Argument rejected. \nFirst command line arguement needs to be numerical value. This arguement dictates runtime.")
			sys.exit(0)
		return args 
	def query(self, q):		# send question to scope, scope returns value
		while True:
			try:
				return self.rig.query(q)
			except pyvisa.errors.VisaIOError:	# no device at address
				try:
					pass
				except TypeError:	# workaround 
					print("Failed to send query. Check syntax, check connection.")
					break
			except ConnectionResetError:
				self.ReConnect()
	def write(self, cmd):	# send command to scope
		while True:
			try:
				return self.rig.write(cmd)
			except pyvisa.errors.VisaIOError:	# no device at address
				try:
					pass
				except TypeError:	# workaround 
					print("Failed to send query. Check syntax, check connection.")
			except ConnectionResetError:
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
	def findPiIP(self):
		try:
			return self.host
		except:
			return ''
	def SetTrigMode(self):
		print('''
Trigger modes are:
  edge, pulse, slope, video, pattern,
  duration, setup/hold, TimeOut, Runt, 
  windows, delay, nth edge, RS232, I2C, SPI
		''')
		print("See DS1000Z user guide pg 5-8 for details on different modes.\n")
		modes = {
		  'edge' : "EDGE",
		  'pulse' : "PULS",
		  'slope' : "SLOP",
		  'video' : "VID",
		  'pattern' : "PATT",
		  'Runt' : "RUNT",
		  'windows' : "WIND",
		  'nth edge' : "NEDG",
		  'delay' : "DEL",
		  'TimeOut' : "TIM",
		  'duration' : "DUR",
		  'setup/hold' : "SHOL",
		  'RS232' : "RS232",
		  'I2C' : "IIC",
		  'SPI' : "SPI"
		}
		while True:
			m = input("Enter desired trigger mode out of options above: ")
			try:
				self.TMcmd = ":TRIG:MODE " + str(modes[m])
				break
			except KeyError:
				print("\nInput not accepted.\nMake sure input matches one of given modes. Input is case and blank space sensitive\n")
		while True:
			try:
				self.rig.write(self.TMcmd)
				break
			except:
				print("Unable to send change mode command. Reconnecting to scope.")
				self.ReConnect()
		print("Trigger mode set to: ", self.rig.query(":TRIG:MODE?\n"))
		return self.TMcmd
	def SetTrigSweep(self):
		print('''
Trigger sweep options are:
  auto, normal, single
		''')
		sweep = {
		  'auto' : "AUTO",
		  'normal' : "NORM",
		  'single' : "SING"
		}
		while True:
			s = input("Enter desired trigger sweep out of options above: ")
			try:
				self.TScmd = ":TRIG:SWE " + str(sweep[s])
				break
			except KeyError:
				print("\nInput not accepted.\Make sure input matches one of given modes. Input is case and blank space sensitive\n")
		while True:
			try:
				self.rig.write(self.TScmd)
				break
			except:
				print("Unable to send sweep mode command. Reconnecting to scope.")
				self.ReConnect()
		print("Trigger mode set to: ", self.rig.query("TRIG:SWE?\n"))
		print("Trigger status: ", self.rig.query("TRIG:STAT?\n"))
		return self.TScmd
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
		try:
			dat_ch = int(dat_ch)
		except:
			print("Cmd Line Arg[3] must be integer")
		if abs(float(dat_ch)) > 4:
			print("Cmd Line Arg[3] must be integer 1, 2, 3, or 4")
			sys.exit(0)
		elif float(dat_ch) == 0:
			print('Cmd Line Arg[3] must be integer 1, 2, 3, or 4')
			sys.exit(0)
		else:
			pass
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
	def GetParams(self):	# get params 
		try:
			self.rig.write(":WAV:XINC?")
			time.sleep(0.01)
			self.xinc = str(self.rig.read_bytes(12))[1:]
			self.params.update({'xinc' :self.xinc})
			self.rig.write(":WAV:XOR?")
			time.sleep(0.01)
			self.xor = str(self.rig.read_bytes(13))[1:]
			self.params.update({'xor' : self.xor})
		except:
			print("Connection Error.\nAttempting Re-Connection...")
			self.ReConnect()
		return self.params
	def GetParams_4ch(self):	# get params 
		self.xinc_4ch = []
		self.xor_4ch = []
		for i in range (1, 5):
			try:
				self.rig.write(":WAV: SOUR CHAN" + str(int(i)))
				self.rig.write(":WAV:XINC?")
				time.sleep(0.01)
				self.xinc_4ch.append(str(self.rig.read_bytes(12))[1:])
				self.rig.write(":WAV:XOR?")
				time.sleep(0.01)
				self.xor_4ch.append(str(self.rig.read_bytes(13))[1:])
			except:
				print("Connection Error.\nAttempting Re-Connection...")
				self.ReConnect()
		self.params.update({'xinc' : self.xinc_4ch})
		self.params.update({'xor' : self.xor_4ch})
		print(self.params)
		return self.params
	def checkdir(self,f, ff):	# check names of files with name f, number output files to avoid overwriting
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
		print("Data output in ./Exp_" + self.exp)
		return [self.out, self.exp]	# output file will be returned as a string with name, number, and extension
	def setupDAQf(self):	# establish output files, experiment number for run 
		check = self.checkdir(self.f, self.ff)
		self.datf = open(check[0], 'w+')
		self.exp = int(float(check[1]))
		return self.exp
	def autogenCSV(self):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		cmd = 'mkdir ./Exp_' + str(self.exp)
		dirct= "Exp_" + str(self.exp)
		subprocess.Popen([cmd], shell = True)
		rawdat = list(self.ReadFile("Exp_" + str(self.exp) + '.txt'))
		#subprocess.Popen(['cd ./'+dirct], shell = True)
		xinc = self.params.get('xinc')
		for i in range(len(rawdat)):
			df = open('./'+dirct+'/Wfm_' + str(i + 1) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
			print("length v array:", len(v))
			df.write(v[0] + '\n')
			for k in range(1,len(v)):
				if v[k].find('\n') == -1:
					ydat.append(v[k])
				else:
					pass
			for k in range(len(ydat)):
				x = float(xinc[1:len(xinc)-1]) * k
				df.write(str(x) + ', ' + ydat[k] + '\n')
			df.close()
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + dirct], shell = True)
	def autogenCSV_4ch(self):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		cmd = 'mkdir ./Exp_' + str(self.exp)
		dirct= "Exp_" + str(self.exp)
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['pwd'], shell = True)
		#subprocess.Popen(['ls'], shell = True)
		rawdat = list(self.ReadFile("Exp_" + str(self.exp) + '.txt'))
		xinc = self.params.get('xinc')
		I = 1
		for i in range(len(rawdat)):
			if i > 4:
				j = (i+1)-((I-1)*4)
			else:
				j = i+1
			if (j)%4 == 0:
				dat_ch = 4
			else:
				if (j)%3 == 0:
					dat_ch = 3
				else:
					if (j)%2 == 0:
						dat_ch = 2
					else:
						dat_ch = 1
			XINC = xinc[dat_ch - 1]
			print(dat_ch)
			df = open('./'+dirct+'/Wfm_' + str(I) + '_Ch_' + str(dat_ch) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
			print("length v array:", len(v))
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
			if dat_ch ==4:
				print("Finished set #", I)
				I = I + 1
			else:
				pass
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + dirct], shell = True)
	def autogenCSV_2ch(self):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		cmd = 'mkdir ./Exp_' + str(self.exp)
		dirct= "Exp_" + str(self.exp)
		subprocess.Popen([cmd], shell = True)
		subprocess.check_output(['pwd'], shell = True)
		rawdat = list(self.ReadFile("Exp_" + str(self.exp) + '.txt'))
		xinc = self.params.get('xinc')
		I = 1
		for i in range(len(rawdat)):
			if i > 2:
				j = (i+1)-((I-1)*4)
			else:
				j = i+1
			if (j)%2 == 0:
				dat_ch = 2
			else:
				dat_ch = 1
			XINC = xinc[dat_ch - 1]
			print(dat_ch)
			df = open('./'+dirct+'/Wfm_' + str(I) + '_Ch_' + str(dat_ch) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
			print("length v array:", len(v))
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
			if dat_ch ==2:
				print("Finished set #", I)
				I = I + 1
			else:
				pass
		subprocess.Popen(["mv Exp_" + str(self.exp) + ".txt " + dirct], shell = True)
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
						vstr = subprocess.check_output(['lxi scpi --address ' + str(self.va)[8:19] + ' ":WAV:DATA?"'], shell = True)
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
		print("Elapsed Time: ", RunTime)
	def Sing4ChanTrigMode(self,acqt, mode, trig_lev):
		"""
		check trigger, get waveform if scope is triggered, reset trigger
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		st = time.perf_counter()
		i = 0	# iteration number
		log = open("ExpLog.txt", 'a+')
		self.SetSingTrig()
		self.TrigLevEdge(trig_lev)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
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
		print("Elapsed Time: ", RunTime)
	def Sing2ChanTrigMode(self,acqt, mode, trig_lev):
		"""
		check trigger, get waveform if scope is triggered, reset trigger
		mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		notes = input("\nEnter any short notes you wish to log with this experiment: ")
		"""
		notes = ''
		st = time.perf_counter()
		i = 0	# iteration number
		log = open("ExpLog.txt", 'a+')
		self.SetSingTrig()
		self.TrigLevEdge(trig_lev)
		while time.perf_counter() - st < float(acqt):
			#print("Acquiring waveform #",i)
			try:
				trig_stat = self.TrigStat()
				if trig_stat == 'RUN\n':
					pass
				elif trig_stat == 'WAIT\n':
					pass
				else:
					print("Acquiring waveform set #", i)
					print(trig_stat)
					parent_conn, child_conn = Pipe()
					for j in range(1, 3):
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
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + " , Single Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ', '+ str(self.params))
		log.close()
		print("Elapsed Time: ", RunTime)

