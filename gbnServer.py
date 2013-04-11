import socket
import sys
import threading
import pickle

class clientHandler(threading.Thread):
	def __init__(self, newTuple):
		threading.Thread.__init__(self)
		self.client = newTuple[0]
		self.address = newTuple[1]
	
	def run(self):
		filename = 's.txt'		
		with open(filename, "rb") as fh:
			b = True
			while b:
				b = fh.read(1)
				self.client.send(b)
				print("Reading b = "+str(b))
		self.client.close()
		
def main():
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = socket.gethostname()
	port = 7734	
	soc.bind((host,port)) 
	soc.listen(5) 
	while True:
		print("Waiting on client....")
		c = clientHandler(soc.accept())
		c.start()



if __name__ == '__main__':
	main()