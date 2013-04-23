import sys
import socket
import time
import struct
import threading

lastSent = 0			#LAST SENT SEQUENCE NUMBER
acked = 0				#SEQUENCE NUMBER OF LAST PACKET ACKED
expectedAck = 1			#SEQUENCE NUMBER NEXT EXPECTED ACK
sendingLock = threading.Lock()
window = {'x':'x'}
startTime = time.time()
endTime = startTime

#Thread that reads the file continuously
class fileReader(threading.Thread):
	def __init__(self, cmdInput, cSock, receiver):
		threading.Thread.__init__(self)
		self.host = cmdInput[0]				#SERVER IP ADDRESS
		self.port = int(cmdInput[1])		#SERVER PORT
		self.file = cmdInput[2]				#FILE TO TRANSMIT
		self.n    = int(cmdInput[3])		#WINDOW SIZE
		self.MSS  = int(cmdInput[4])		#MAXIMUM SEGMENT SIZE	
		self.sock = cSock
		self.r = receiver
		self.currSeq = 0
		self.start()		
	
	'''def computeChecksum(self, data):
		sum = 0
		for i in range(0, len(data), 2):
			if i+1 < len(data):
				data16 = ord(data[i]) + (ord(data[i+1]) << 8)		#To take 16 bits at a time
				interSum = sum + data16
				sum = (interSum & 0xffff) + (interSum >> 16)		#'&' to ensure 16 bits are returned
		return ~sum & 0xffff										#'&' to ensure 16 bits are returned'''
		
		
	def computeChecksum(self,data):
		pos = len(data)
		if (pos & 1):  # If odd...
			pos -= 1
			sum = ord(data[pos])  # Prime the sum with the odd end byte
		else:
			sum = 0
 
		#Main code: loop to calculate the checksum
		while pos > 0:
			pos -= 2
			sum += (ord(data[pos + 1]) << 8) + ord(data[pos])
 
		sum = (sum >> 16) + (sum & 0xffff)
		sum += (sum >> 16)
 
		result = (~ sum) & 0xffff #Keep lower 16 bits
		result = result >> 8 | ((result & 0xff) << 8)  # Swap bytes
		return result
		
				
	def formPacket(self, data1, seq):
		#32 bit sequence number
		#16 bit check of the data part
		#16 bit 0101010101010101 -- Indicates data packet(in int 21845)
		#data = str(data1,'UTF-8',errors='replace')
		data1 = data1.encode('ISO-8859-1','ignore')
		data = data1.decode('ISO-8859-1','ignore')
		seqNum = struct.pack('=I',seq)
		checksum = struct.pack('=H',self.computeChecksum(data))		#Computes the checksum of data
		dataIndicator = struct.pack('=H',21845)
		#packet = seqNum+checksum+dataIndicator+bytes(data,'UTF-8')
		packet = seqNum+checksum+dataIndicator+data.encode('ISO-8859-1','ignore')
		#packet = seqNum+checksum+dataIndicator+data
		return packet
	
	def run(self):
		self.rdt_send()	
		
	def checkForTimeout(self):
		global acked
		global window
		global sendingLock

		sendingLock.acquire()
		if len(window) > 1 and acked < self.currSeq:
			firstPacket = window[acked+1]
			packet = firstPacket[0]
			sentTime = firstPacket[1]		
			if time.time() - sentTime >= 0.2:			#RETRANSMISSION TIME
				for i in range(acked+1, self.currSeq+1):
					packet = window[i][0]
					print('TIMEOUT, SEQUENCE NUMBER = '+str(i))					
					self.sock.sendto(packet,(self.host, self.port))
					window[i] = (packet,time.time())
		sendingLock.release()
		
	
	def rdt_send(self):
		global lastSent
		global acked
		global window
		global sendingLock
		global startTime
		
		fileHandle = open(self.file,'r')
		sendMsg = ''
		#sendMsg = bytes('','UTF-8')
		b = True
		done = 0
		while b:
			b = fileHandle.read(1)
			#sendMsg += str(b,'UTF-8')
			#sendMsg += str(b,'ISO-8859-1')
			sendMsg += b
			if not b:
				done = 1
			if len(sendMsg) == self.MSS or (not b):		
				while self.currSeq - acked >= self.n:
					#sendingLock.acquire()
					self.checkForTimeout()
					#sendingLock.release()
					
				'''	sendingLock.acquire()
				sender(self.sock, self.host, self.port, sendMsg, currSeq)    #Thread spawned to handle a single packet				
				currSeq += 1
				sendingLock.release()'''
				
				self.currSeq += 1
				if self.currSeq == 1:
					startTime = time.time()
				packet = self.formPacket(sendMsg, self.currSeq)
				sendingLock.acquire()
				window[self.currSeq] = (packet,time.time())
				sendingLock.release()
				self.sock.sendto(packet,(self.host, self.port))
				sendMsg = ''
				#sendMsg = bytes('','UTF-8')


		sendMsg = '00000end11111'
		self.currSeq += 1
		packet = self.formPacket(sendMsg, self.currSeq)
		sendingLock.acquire()
		window[self.currSeq] = (packet,time.time())
		sendingLock.release()
		self.sock.sendto(packet,(self.host, self.port))
		
		#sender(self.sock, self.host, self.port, sendMsg,self.currSeq)		#Thread spawned to send the end packet'''
		lastSent = self.currSeq
		while acked < lastSent:
			self.checkForTimeout()
		fileHandle.close()


		
		
#Thread Class to receive the ACK Packets from the Server
class receiver(threading.Thread):
	def __init__(self, cmdInput, cSock):		
		threading.Thread.__init__(self)
		self.host = cmdInput[0]
		self.port = int(cmdInput[1])
		self.file = cmdInput[2]
		self.n    = int(cmdInput[3])
		self.MSS  = int(cmdInput[4])
		self.sockAddr = cSock
		self.start()
	
	def parseMsg(self, msg):
		sequenceNum = struct.unpack('=I', msg[0:4])			#Sequence Number Acked by the server
		zero16 = struct.unpack('=H', msg[4:6])				#16 bit field with all 0's
		identifier = struct.unpack('=H', msg[6:])			#16 bit field to identify the ACK packets
		return sequenceNum, zero16, identifier
		
	def run(self):
		print('Receiver Spawned')
		global lastSent
		global acked		
		global expectedAck
		global sendingLock

		try:
			while lastSent <= 0 or  acked < lastSent:			
				ackReceived, server_addr = self.sockAddr.recvfrom(2048)			#Receives the ACK packets 
				sequenceNum , zero16, identifier = self.parseMsg(ackReceived)	
				
				#16 bit identifier field to identify the ACK packets - 1010101010101010 [in int 43690]		
				#if int(identifier[0]) == 43690 and expectedAck == int(sequenceNum[0]):
				if int(identifier[0]) == 43690:
					sendingLock.acquire()
					acked = int(sequenceNum[0])
					#print('Acked :'+str(sequenceNum[0]))
					del window[int(sequenceNum[0])]
					expectedAck = acked+1
					sendingLock.release()					
				
		except:
			print('Server closed its connection')
			self.sockAddr.close()
		print('Receiver Ended')
			
def main():
	global endTime
	host = sys.argv[1]
	port = int(sys.argv[2])
	cliPort = int(input('Client Port ='))
	cliSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	cliSocket.bind(('',cliPort)) 
	
	startTime = time.time()
	ackReceiver = receiver(sys.argv[1:], cliSocket)					#Thread that receives ACKs from the Server
	fileHandler = fileReader(sys.argv[1:],cliSocket, ackReceiver) 	#Thread that reads the file and sending of packets
	fileHandler.join() 			#Main thread waits till the sender finishes
	ackReceiver.join()			#Main thread waits till the ACK receiver finishes
	endTime = time.time()
	print('=======================================')
	print('HOST:'+host)
	print('PORT:'+str(port))
	print('N:'+sys.argv[4])
	print('MSS:'+sys.argv[5])
	print('Total Time Taken:'+str(endTime-startTime))
	print('=======================================')
	if cliSocket:
		cliSocket.close()
		
	
if __name__ == '__main__':	
	main()	


