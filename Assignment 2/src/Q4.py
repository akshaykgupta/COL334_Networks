import sys, socket, json, time, thread, threading

list_of_requests = [] # list of dictionary objects.

#threading for TCP sockets:

class tcp_thread(threading.Thread):
	def __init__(self, threadID, start, end):
		threading.Thread.__init(self)
		self.start = start
		self.end = end
		self.threadID = threadID
		
	def processObject(obj):
		resultString = "GET " + SOMETHING + " HTTP1.1\r\nConnection:keep-alive\r\n\r\n"
		return resultString
	
	def run(self):
		#I need to start a socket, then close it later.
		global list_of_requests
		connection = socket.socket(AF_INET , SOCK_STREAM, 0) #a tcp socket.
		#IMPORTANT NOTE : For the last Request, Connection header needs to be "close"
		for idx in range(self.start,self.end):
			request = processObject(list_of_requests[idx])
			portno = 80 # Check
			connection.connect((request,portno))




#Things I need for a HTTP Get request are :



def extract_requests_har(infile):
	f = open(infile) #open the file!
	har_data = json.parse(f)['log']
	#entries in har_data are : version, creator, browser, pages, entries
	

def main(infile, n_tcp, n_obj_per_tcp):
	if ( sys.argv[1]="har" ):
		extract_requests_har(infile)
	elif ( sys.argv[1]="obj" ):
		extract_requests_obj(infile)
	else:
		sys.exit("Error! Wrong input mode! Please use har for .har file and obj for object trees!\n") #exit due to error.

	#ASSERT : we have list of requests.



if __name__ == '__main__':
	main(sys.argv[2] , sys.argv[3], sys.argv[4]) #argv[2] is HAR file/ OBJT file. argv[3] is #of tcp connections. argv[4] is number of objects per connection.