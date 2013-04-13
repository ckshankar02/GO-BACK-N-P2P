import sys
import socket
import threading

#### ack indications in int 43690

def main():
	#port filename probability
	port = int(sys.argv[1])
	filename = sys.argv[2]
	prob = sys.argv[3]
	flag = True
	soc  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	host = socket.gethostname()
	soc.bind((host,port)) 
	fileHandler = open(filename,'w')
	while flag:	
		receivedMsg, sender_addr = soc.recvfrom(25)	
		msg = receivedMsg.decode('UTF-8')
		fileHandler.write(msg)
		if msg != 'end':
			print('Sending Acknowledge')
			ackPacket = bytes('packet acknowledged','UTF-8')		
			soc.sendto(ackPacket,sender_addr)
		else:
			flag = False
	fileHandler.close()
	#soc.close()	
	

if __name__ == '__main__':	
	main()