#!/usr/bin/env python3
# Rebecca Nishide, updated 11/23/2020

import subprocess
import sys
import re 

class DataTransfer:
	def __init__(self):
		self.ar = list(sys.argv)
		self.args = []
		for i in range(1, len(self.ar)):
			try:
				float(self.ar[i])
				self.args.append(str(self.ar[i]))
			except:
				pass
		self.n_args = len(self.args)
	def ReadFile(self, infile):
		read = open(infile, 'r')
		lines = read.readlines()
		read.close()
		return lines
	def GetUpload_FN_List(self, exp_n):
		cmd = "ls ./Exp_" + str(exp_n)
		contents = subprocess.check_output([cmd], shell = True)
		contents = contents.decode('utf-8')
		contents = contents.strip()
		contents = contents.split('\n')
		return list(contents)
	def UploadExperiment(self, infile, exp_n):
		try:
			data = self.ReadFile("./Exp_" + str(exp_n) + "/" + infile)
		except FileNotFoundError:
			print("Data file for Exp_", exp_n, "not found in directory")
			return "failed"
		outfile = "/var/www/html/RIGOL/Exp_" + exp_n + "/" + str(infile)[:len(str(infile)) - 3] + "php"
		OF = open(outfile, 'w+')
		OF.write("<!DOCTYPE html>")
		OF.write("\n<html>\n<body>\n")
		for i in data:
			i = i.strip()
			OF.write('\n<?php\necho "')
			OF.write(i)
			OF.write('";\n?><br>')
		OF.write("\n</body>\n</html>\n")
		OF.close()
	def UploadData(self):
		for i in self.args:
			subprocess.Popen(["mkdir /var/www/html/RIGOL/Exp_" + str(i)], shell = True)
			ls = subprocess.check_output(["ls /var/www/html/RIGOL"], shell = True)
			try:
				FN_List = self.GetUpload_FN_List(i)
				for j in FN_List:
					self.UploadExperiment(str(j), str(i))
				print("\nDone Uploading Experiment ", str(i))
			except:
				print("Unable to Upload Experiment ", str(i))
	def GetDownload_FN_List(self, IP, exp_n):
		try:
			CheckRIGOL = "curl http://" + str(IP) + "/RIGOL/Exp_" + str(exp_n) + "/"
			contents = subprocess.check_output([CheckRIGOL], shell = True).decode('utf-8')
		except:
			print("Not connected to correct network. Scope data is on scope's local server; ensure you are connected to the correct network...\nExiting...")
		contents = re.split('<|>|=|"', contents)
		FILE_LIST = []
		for i in contents:
			if i.find(".php") != -1:
				FILE_LIST.append(i)
		self.FILE_SET = set(FILE_LIST)
		self.FN_LIST = []
		for i in self.FILE_SET:
			self.FN_LIST.append(i[:len(i)-4])
		return self.FN_LIST
	def WriteBackData(self, IP, FN, extension, exp_n):
		CurlFile = "curl http://" + str(IP) + "/RIGOL/Exp_" + str(exp_n) + "/" + str(FN) + ".php"
		OutFile = "./Exp_" + str(exp_n) + "/" +  str(FN) + "." + extension
		DF = open(OutFile, 'w+')
		data = subprocess.check_output([CurlFile], shell = True)
		data = data.decode('utf-8')
		data = list(re.split('<br>', data))
		for k in range(len(data) - 1):
			if k == 0:
				L1 = list(data[k].split('\n\n'))
				DF.write(L1[1])
			else:
				DF.write(data[k])
		DF.close()
	def DownloadData(self, IP):
		for i in self.args:
			subprocess.Popen(["mkdir ./Exp_" + str(i)], shell = True)
			subprocess.check_output(['ls'], shell = True)
			FN_LIST = self.GetDownload_FN_List(IP, i)
			for j in FN_LIST: 
				if j.find('Wfm') == -1:
					self.WriteBackData(IP, j, 'txt', i)
				else:
					self.WriteBackData(IP, j, 'csv', i)
 
