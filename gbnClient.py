import socket
import sys
def main():
	cliSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = socket.gethostname()
	port = 7734
	f = open('newtxt2.txt','w')
	cliSoc.connect((host,port))
	data = True
	while data:
		data = cliSoc.recv(1024) #buffer size is the argument.
		if data:
			decodedData = data.decode('UTF-8') 
			f.write(decodedData)
	f.close()
	while 1:
		pass
		
if __name__ == '__main__':	
	main()