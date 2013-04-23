import sys
import socket
import struct
import random
import threading

def parseMsg(msg):								#Parsing the Message received from client
	header = msg[0:8]
	data = msg[8:]	
	sequenceNum = struct.unpack('=I',header[0:4])		
	checksum = struct.unpack('=H',header[4:6])
	identifier = struct.unpack('=H',header[6:])
	dataDecoded = data.decode('ISO-8859-1','ignore')
	return sequenceNum, checksum, identifier, dataDecoded
	
def formAckPackets(seqAcked):
	seqNum 		 = struct.pack('=I', seqAcked)	#SEQUENCE NUMBER BEING ACKED	
	zero16 	 	 = struct.pack('=H', 0)
	ackIndicator = struct.pack('=H',43690)		#ACK INDICATOR - 1010101010101010[INT 43690]
	ackPacket = seqNum+zero16+ackIndicator
	return ackPacket

'''def verifyChecksum(data, checksum):
	sum = 0	
	for i in range(0, len(data), 2):
		if i+1 < len(data):
			data16 = ord(data[i]) + (ord(data[i+1]) << 8)		#To take 16 bits at a time
			interSum = sum + data16
			sum = (interSum & 0xffff) + (interSum >> 16)		#To ensure 16 bits
	currChk = sum & 0xffff 
	#result = currChk & checksum
	result = currChk
	if result == checksum:
		return True
	else:
		return False'''
		
def verifyChecksum(data, checksum):
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
	#print(result)
	if result == checksum:
		return True
	else:
		return False
	#return True
	
def main():
	#port filename probability
	
	port = int(sys.argv[1])		#PORT ON WHICH SERVER WILL ACCEPT UDP PACKETS
	filename = sys.argv[2]		#NAME OF THE NEW FILE CREATED
	prob = float(sys.argv[3])	#PACKET DROP PROBABILITY
	expSeqNum = 1				
	flag = True
	
	soc  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	host = socket.gethostname()
	soc.bind((host,port)) 
	
	fileHandler = open(filename,'w')
	
	while flag:	
		receivedMsg, sender_addr = soc.recvfrom(1024)			#Receive packets sent by client
		sequenceNum, checksum, identifier, data = parseMsg(receivedMsg) 
		if random.uniform(0,1) > prob:							#PACKET MAY BE DROPPED BASED ON RANDOM VALUE
			if expSeqNum == int(sequenceNum[0]):				#If the expected Packet
				chksumVerification = verifyChecksum(data, int(checksum[0]))
				if chksumVerification == True:
					if data != '00000end11111':					#If not the END Packet
						fileHandler.write(data)					#Write to FILE
						#print(data)
						ackPacket = formAckPackets(int(sequenceNum[0]))		#Generating ACK Packet
						soc.sendto(ackPacket,sender_addr)					#Sending ACK
						expSeqNum += 1
					else:
						flag = False
						ackPacket = formAckPackets(int(sequenceNum[0]))		#Generating ACK Packet
						soc.sendto(ackPacket,sender_addr)					#Sending ACK
					
		else:
			print('PACKET LOSS, SEQUENCE NUMBER = '+str(sequenceNum[0]))	#Packet dropped if randomValue <= probability
				
			
	fileHandler.close()
	print('==========================================')
	print('File Received Successfully at the Server')
	print('p:'+str(prob))
	print('==========================================')
	soc.close()	
	
if __name__ == '__main__':	
	main()