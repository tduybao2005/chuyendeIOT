#!/usr/bin/env python3

import time
import sys
import serial

class LORA_USB():
	debug_on = 0
	def __init__(self, COM='COM14', address = 1):
		self.M_address = address
		self.ser = serial.Serial()
		self.ser.baudrate = 115200
		self.ser.port = COM
		self.ser.open()
		

	def write_data(self, node_add, reg_add, data):
		if self.debug_on:
			print ("Send: data")
		#			   | 0     | 1 |   2  |   3 |  4  |
		# data frame = |NodeAdd|CMD|RegAdd|DataH|DataL|
		dataH = (data & 0xff00) >> 8
		dataL = data & 0x00ff
		data_send = [0, node_add, node_add, 255, self.M_address, 1, reg_add, dataH, dataL, 254, 13]
		if self.debug_on:
			print (data_send)
		self.ser.write(bytearray(data_send)) # Send data
		time.sleep(0.1) # there must be a better solution but sleep() works
		
	def read_data(self, node_add, reg_add):
		self.var=0
		#			   | 0     | 1 |   2  |   3 |  4  |
		# data frame = |NodeAdd|CMD|RegAdd|DataH|DataL|
		data_send = [0, node_add, node_add, 255, self.M_address, 0, reg_add, 0, 0, 254, 13]
		if self.debug_on:
			print (data_send)
		self.ser.write(bytearray(data_send)) # Send data
		time.sleep(0.1)
		
		start_time = time.time()
		while (time.time() - start_time < 3):
			if self.ser.in_waiting == 2:
				buffer = self.ser.read(2)
				dataH = buffer[0]
				dataL = buffer[1]
				return (dataH*256+dataL)
			elif self.ser.in_waiting > 2:
				buffer11 = self.ser.read_all()
				return -1
			pass
		return -1
	

if __name__ == "__main__":
	lora = LORA_USB(COM='COM14', address=8)
	lora.debug_on = 0
	#print(lora.read_data(1,4))
	#lora.write_data(1,8,1)
	while True:
		lora.write_data(1,9,1)
		lora.write_data(2,9,1)
		time.sleep(0.1)
		lora.write_data(1,9,0)
		lora.write_data(2,9,0)
		time.sleep(0.1)

		# print(lora.read_data(1,4))
		# print(lora.read_data(1,5))
		# print(lora.read_data(1,6))
		# print('')
		# print(lora.read_data(2,4))
		# print(lora.read_data(2,5))
		# print(lora.read_data(2,6))
		# time.sleep(0.1)

		# lora.write_data(3,8,lora.read_data(3,4))
		# lora.write_data(3,9,lora.read_data(3,5))

