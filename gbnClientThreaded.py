import sys
import socket
import time
import struct
import threading

lastSent = 0			#LAST SENT SEQUENCE NUMBER
acked = 0				#SEQUENCE NUMBER OF LAST PACKET ACKED
expectedAck = 0			#SEQUENCE NUMBER NEXT EXPECTED ACK
sendingLock = threading.Lock()

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
		self.start()		
		
	def run(self):
		self.rdt_send()	
		
	def rdt_send(self):
		fileHandle = open(self.file,'rb')
		currSeq = 0
		global lastSent
		global acked
		sendMsg = ''
		b = True
		while b:
			b = fileHandle.read(1)
			sendMsg += str(b,'UTF-8')
			if len(sendMsg) == self.MSS or (not b):		
				while currSeq-acked >= self.n:
					pass
				sender(self.sock, self.host, self.port, sendMsg, currSeq)    #Thread spawned to handle a single packet
				currSeq += 1
				sendMsg = ''
						
		sendMsg = '00000end11111'
		sender(self.sock, self.host, self.port, sendMsg,currSeq)		#Thread spawned to send the end packet
		lastSent = currSeq
		fileHandle.close()

		
#Thread Class to handle the sending of a single packet
class sender(threading.Thread):
	def __init__(self, cSock, hst, prt, msg, s):
		threading.Thread.__init__(self)
		self.timer = time.time()
		self.data = msg				#DATA OF 1 MSS SIZE TO BE SENT
		self.seqNum = s				#SEQUENCE NUMBER OF THE PACKET
		self.sock = cSock
		self.host = hst				#SERVER IP ADDRESS
		self.port = prt				#SERVER PORT
		self.start()
	
	def computeChecksum(self, data):
		sum = 0
		for i in range(0, len(data), 2):
			if i+1 < len(data):
				data16 = ord(data[i]) + (ord(data[i+1]) << 8)		#To take 16 bits at a time
				interSum = sum + data16
				sum = (interSum & 0xffff) + (interSum >> 16)		#'&' to ensure 16 bits are returned
		return ~sum & 0xffff										#'&' to ensure 16 bits are returned
				
	def formPacket(self, data, seq):
		#32 bit sequence number
		#16 bit check of the data part
		#16 bit 0101010101010101 -- Indicates data packet(in int 21845)
		seqNum = struct.pack('=I',seq)
		checksum = struct.pack('=H',self.computeChecksum(data))		#Computes the checksum of data
		dataIndicator = struct.pack('=H',21845)
		packet = seqNum+checksum+dataIndicator+bytes(data,'UTF-8')
		return packet
	
	def run(self):
		global acked
		sendingLock.acquire()
		packet = self.formPacket(self.data, self.seqNum)				#Packets are created here
		self.sock.sendto(packet,(self.host, self.port))
		sendingLock.release()
		try:
			while acked < self.seqNum:
				diff = time.time() - self.timer
				if  diff < 5:									#RETRANSMISSION time = 5 seconds
					pass
				else:
					if acked < self.seqNum:								#Rechecking the ACK
						print('TIMEOUT, SEQUENCE NUMBER = '+str(self.seqNum))
						self.sock.sendto(packet,(self.host, self.port))	#RETRANSMISSION of time-out packets(No ACK Received)
						self.timer = time.time()
		except:
			print('Server closed its connection')
			self.sock.close()
		
		
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
		try:
			while lastSent <= 0 or  acked < lastSent:			
				ackReceived, server_addr = self.sockAddr.recvfrom(2048)			#Receives the ACK packets 
				sequenceNum , zero16, identifier = self.parseMsg(ackReceived)
				
				#16 bit identifier field to identify the ACK packets - 1010101010101010 [in int 43690]		
				if int(identifier[0]) == 43690 and expectedAck == int(sequenceNum[0]):
					acked = int(sequenceNum[0])
					expectedAck = acked+1
				#print('Packet of Seq No.'+str(sequenceNum[0])+' Acked')
				
		except:
			print('Server closed its connection')
			self.sockAddr.close()

			
def main():
	host = sys.argv[1]
	port = int(sys.argv[2])
	cliSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	cliSocket.bind(('',3334)) 
	
	ackReceiver = receiver(sys.argv[1:], cliSocket)					#Thread that receives ACKs from the Server
	fileHandler = fileReader(sys.argv[1:],cliSocket, ackReceiver) 	#Thread that reads the file and sending of packets
	fileHandler.join() 			#Main thread waits till the sender finishes
	ackReceiver.join()			#Main thread waits till the ACK receiver finishes
	if cliSocket:
		cliSocket.close()
		
	
if __name__ == '__main__':	
	main()	


