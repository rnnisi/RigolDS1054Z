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
		self.dat = "Wfm_1.txt"
		self.acq = "AcqTimes_1.csv"
		self.datff = "'Wfm_' + str(i) + '.txt'"
		self.acqff = "'AcqTimes_' + str(i) + '.csv'"
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
		try:
				self.rig = self.rm.open_resource(self.va)
				print("Connected to: ",self.rig.write("*IDN?"))
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
						return self.va
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
			print("Program requires a different number if command line arguements. First should be desired run time in seconds, second 'LXI' or 'normal' to dictate DAQ method. Only use 'LXI' if lxi-tools is properly installed. Third should be CHAN# to indicate the channel you want to read data from.\nCheck manual or python runfile for more specifications.")
			sys.exit(0)
		else:
			pass
		try:
			float(args[1])
		except ValueError:
			print("First command line arguement needs to be numerical value. This arguement dictates runtime.")
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
	def SetupNormCollection(self, n, dat_ch):	# use if scope is in auto
		try:
			self.rig.timeout = 30000
			self.rig.write(":WAV:MODE NORM")
			self.rig.write(":WAV:SOUR " + dat_ch)
			self.rig.write(":WAV:FORM ASC")
			self.rig.write("WAV:STAR 1")
			self.rig.write("wav:STOP "+ str(n))
		except:
			print("Unable to send parameters to scope. Reconnecting")
			self.Connect()
	def SetupNormCollection(self, n, dat_ch):	# use if scope is in auto
		try:
			self.rig.timeout = 3000
			self.rig.write(":WAV:MODE NORM")
			self.rig.write("WAV:SOUR " + dat_ch)
			self.rig.write(":WAV:FORM ASC")
			self.rig.write("WAV:STAR 1")
			self.rig.write("wav:STOP "+ str(n))
		except:
			print("Unable to send parameters to scope. Reconnecting")
			self.Connect()
	def SetupSingTrigCollection(self, n, dat_ch):	# use for single trigger, reading waveforms when scope is stopped
		try:
			self.rig.timeout = 3000
			self.rig.write(":WAV:MODE RAW")
			self.rig.write("WAV:SOUR " + dat_ch)
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
	def GetVoltages(self, n):	# get voltages, no lxi
		q = (":WAV:DATA?\n")		
		self.rig.write(q)
		time.sleep(0.01)
		self.a = self.rig.read_bytes(int(n)*12 + int(n)-1 + 12)
		return self.a
	def GetParams(self):	# get params 
		try:
			self.rig.write(":WAV:XINC?")
		except:
			print("Unable to send parameters to scope. Reconnecting")
			self.ReConnect()
		time.sleep(0.01)
		self.xinc = str(self.rig.read_bytes(12))[1:]
		self.params.update({'xinc' :self.xinc})
		self.rig.write(":WAV:XOR?")
		time.sleep(0.01)
		self.xor = str(self.rig.read_bytes(13))[1:]
		self.params.update({'xor' : self.xor})
		return self.params
	def checkdir(self,f, ff):	# check names of files with name f, number output files to avoid overwriting
		i = 2				# format for f should be : NAME_n.txt with n = 1, 2, 3.....
		if os.path.exists(f) == False:
			out = open(f, 'w+')
		else:
			while os.path.isfile(f) == True:
				f = eval(ff)
				i = i+1
				os.path.isfile(f)
		self.out = str(f)
		self.exp = str(i)
		return [self.out, self.exp]	# output file will be returned as a string with name, number, and extension
	def setupDAQf(self):	# establish output files, experiment number for run 
		self.datf = open(self.checkdir(self.dat, self.datff)[0], 'w+')
		self.exp = int(float(self.checkdir(self.dat, self.datff)[1]) - 2)
		return self.datf, self.exp
	def autogenCSV(self):	# automatically process raw data output, make a directory with csv's for every waveform collected
		self.datf.close()
		cmd = 'mkdir Exp_' + str(self.exp)
		dirct = "Exp_" + str(self.exp)
		subprocess.Popen([cmd], shell = True)
		rawdat = list(self.ReadFile("Wfm_" + str(self.exp) + '.txt'))
		subprocess.Popen(['cd ./'+dirct], shell = True)
		xinc = self.params.get('xinc')
		for i in range(len(rawdat)):
			df = open('./'+dirct+'/Wfm_' + str(i + 1) + '.csv', 'w+')
			ydat = []
			v = list(str(rawdat[i]).split(','))
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
	def TimeOut(self):	# timeout feature to force exit if anything gets stuck due to out of control/external causes
		time.sleep(30)	# set timeout for operations defined in this class
		print("\nData Acq timed out.\nCheck if scope is powered.\nExiting program.")
		self.datf.close()
		_thread.interrupt_main()
		sys.exit(0)
	def WriteOutWv(self, n, child_conn, mode):	# option to use lxi software or self contained capabilities 
		st = time.perf_counter()
		self.datf.write("StartTime: " + str(st) + ',' )
		to = Thread(target = self.TimeOut)
		to.setDaemon(True)	# let timeout run in background. it will interrupt if parent gets stuck.
		to.start()
		try:
			if mode == 'LXI':
				print("\nNOTE: LXI GIVES NONFATAL ERROR. DISREGARD.")
				attempt = 0 
				while attempt < 10:
					try:
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
				vstr = self.GetVoltages(n)
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
				os._exit(0)
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
	def GeneralAuto(self, acqt, mode):	# collects waveforms as fast as it can, no trigger consideration 
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
				p1 = Process(target = self.WriteOutWv, args = ('1100', child_conn, mode))
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
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", Auto Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ", Notes = " + str(notes))
		log.close()
		print("Elapsed Time: ", RunTime)
	def ForceSingTrigMode(self,acqt, mode):	# forces trigger and collects waveforms during stop mode, resets, as fast as possible
		#mode = input("Enter 'LXI' if you wish to use LXI for data acquisition, else enter 'normal': ")
		#notes = input("\nEnter any short notes you wish to log with this experiment: ")
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
				p1 = Process(target = self.WriteOutWv, args = ('1100',child_conn, mode))
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
		log.write("\nExperiment # " + str(self.exp) + ": " + time.asctime() + ", Single Trigger, mode = " + str(mode) + ", AcqTime = " + str(RunTime) + ", Waveforms Collected = " + str(i) + ", Notes = " + str(notes))
		log.close()
		print("Elapsed Time: ", RunTime)
