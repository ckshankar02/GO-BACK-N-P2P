import sys
import socket
import time
import threading

lastSent = 0
acked = 0

class fileReader(threading.Thread):
	def __init__(self, cmdInput, cSock, receiver):
		threading.Thread.__init__(self)
		self.host = cmdInput[0]
		self.port = int(cmdInput[1])
		self.file = cmdInput[2]
		self.n    = int(cmdInput[3])
		self.MSS  = int(cmdInput[4])
		self.sock = cSock
		self.r = receiver
		self.start()
		#self.seqNum = 0
		
		
	def run(self):
		self.rdt_send()
	
	def computeChecksum(self, data):
		pass
	
	def formPacket(self, data, seq):
		#32 bit sequence number
		#16 bit check of the data part
		#16 bit 0101010101010101 -- Indicates data packet(in int 21845)
		seqNum = '{0:032b}'.format(seq)
		checksum = self.computeChecksum(data)
		dataIndicator = '{0:016b}'.format(21845)
		packet = seqNum+checksum+dataIndicator+data
		
		
	def rdt_send(self):
		fileHandle = open(self.file,'rb')
		i = 0
		global lastSent
		global acked
		sendMsg = ''
		b = True
		while b:
			b = fileHandle.read(1)
			sendMsg += str(b, 'UTF-8')
			if len(sendMsg) == self.MSS:
				#packet = formPacket(c, self.seqNum)
				#packet = bytes(sendMsg,'UTF-8')
				#self.seqNum += 1		
				while lastSent - acked >= self.n:
					pass
				sender(sendMsg,i)
				i += 1
				#self.sock.sendto(packet,(self.host, self.port))
				sendMsg = ''
		self.sock.sendto(bytes('end','UTF-8'),(self.host, self.port))	
		lastSent = i
		fileHandle.close()

class sender(threading.Thread):
	def __init__(self, msg, s):
		threading.Thread.__init__(self)
		self.timer = time.time()
		self.data = msg
		self.seqNum = s
		self.start()
		
	def run(self):
		global acked
		packet = bytes(sendMsg,'UTF-8')
		self.sock.sendto(packet,(self.host, self.port))
		while acked < self.seqNum:
			diff = time.time() - self.timer
			if  diff < 5:
				pass
			else:
				if acked < self.seqNum:
					self.sock.sendto(packet,(self.host, self.port))
				
class receiver(threading.Thread):
	def __init__(self, cmdInput, cSock):		
		threading.Thread.__init__(self)
		self.host = cmdInput[0]
		self.port = int(cmdInput[1])
		self.file = cmdInput[2]
		self.n    = int(cmdInput[3])
		self.MSS  = int(cmdInput[4])
		self.sockAddr = cSock
		#self.senderRef = sender
		self.start()
		
		
	def run(self):
		print('Receiver Spawned')
		global lastSent
		global acked		
		while lastSent <= 0 or  acked < lastSent:			
			ackReceived, server_addr = self.sockAddr.recvfrom(2048)	
			acked += 1
			print(ackReceived.decode('UTF-8'))
		
def main():
	host = sys.argv[1]
	port = int(sys.argv[2])
	cliSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	cliSocket.bind(('',3334)) 
	ackReceiver = receiver(sys.argv[1:], cliSocket)
	fileHandler = fileReader(sys.argv[1:],cliSocket, ackReceiver)
	ackReceiver.join()
	dataSender.join()
	cliSocket.close()
	

	
	
	
if __name__ == '__main__':	
	main()	


