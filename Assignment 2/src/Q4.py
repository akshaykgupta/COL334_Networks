import sys, socket, json, time, thread, threading, os, mutex

filemutex = mutex.mutex()
my_lock = threading.Lock()
your_lock = threading.Lock()
oid = 0

def get_filestream( fullpath ):
	directory = os.path.dirname(fullpath) #Will not having a directory part create a problem? Like, will directory = "" create problems?
	if not os.path.exists(directory):
		os.makedirs(directory)
	return;

class handle_objects(threading.Thread):

	def __init__(self,domain_name,list_of_objects):
		threading.Thread.__init__(self)
		self.domain = domain_name
		self.list_of_objects = list_of_objects

	def run(self):
		#TODO: Pretty Printing.
		global my_lock
		global oid
		connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
		connection.connect((self.domain,80))
		filenames = []
		for idx in range(0,len(self.list_of_objects)):
			request = self.list_of_objects[idx]
			all_data = ''
			if(idx != len(self.list_of_objects) -1):
				request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\nConnection: keep-alive\r\n\r\n"
			else:
				request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\nConnection: close\r\n\r\n"
			filenames.append(request)
			connection.send(request_string)
		data = connection.recv(1024)
		all_data = ''
		while(len(data)!=0):
			all_data = all_data + data
			try:
				connection.settimeout(2.0)
				data = connection.recv(1024)
				connection.settimeout(None)
			except:
				data = ''
		start_id = -1
		end_id = -1
		with my_lock:
			start_id = oid	
			g = open('Mapping.txt','a')
			for request in filenames:
				g.write(str(oid) + '\t' + request.split('//')[1] +'\n')
				oid = oid + 1
			end_id = oid
			g.close()
		fileNumber = start_id
		while(len(all_data)!=0):
			length_of_file = -1	
			all_data = all_data.split('\n')
			counter = -1
			length_of_file = 0
			for idx in range(0,len(all_data)):
				counter = idx
				line = all_data[idx].rstrip('\r')
				if(line == ''):
					break
				else:
					line = line.split(':')
					if(len(line) != 1):
						if(line[0] =='Content-Length'):
							length_of_file = eval(line[1])

			all_data = '\n'.join(all_data[counter+1:len(all_data)])
			f = open('dl/' + str(fileNumber)+'.txt','w')
			if(length_of_file == -1):
				# The very special case of no Content-length
				#Everyone who uses HTTP/2 and does not set Content-Length can politely fuck off
				all_data = all_data.split('HTTP/1')
				f.write(all_data[0])
				if(len(all_data) > 1):
					all_data = 'HTTP/1' + 'HTTP/1'.join(all_data[1:len(all_data)])
				else:
					all_data = ''
			else:
				for idx in range(0,length_of_file):
					if(idx < len(all_data)):
						f.write(all_data[idx])
					else:
						break
				if(len(all_data) > length_of_file):
					all_data = all_data[length_of_file:len(all_data)]
				else:
					all_data = ''
			fileNumber = fileNumber + 1
		
		while(fileNumber < end_id):
			f = open('dl/' + str(fileNumber)+'.txt','w')
			fileNumber = fileNumber + 1
			#Store all_data somewhere.
		connection.close()

			

class handle_domain(threading.Thread):

	def __init__(self,domain_name,list_of_objects,maxTCP,maxOBJ):
		threading.Thread.__init__(self)
		self.domain = domain_name
		self.list_of_objects = list_of_objects
		self.maxTCP = maxTCP
		self.maxOBJ = maxOBJ
	
	def run(self):
		low = 0
		while(True):
			thread_list = []
			for i in range(0,self.maxTCP):
				high = self.maxOBJ + low
				if(high > len(self.list_of_objects)):
					high = len(self.list_of_objects)
				thread = handle_objects(self.domain,self.list_of_objects[low:high])
				thread.start()
				thread_list.append(thread)
				low = high
				if(len(self.list_of_objects) == low):
					break
			#So that only maxTCP connections are active at any given time.
			for thread in thread_list:
				thread.join()
			if(low == len(self.list_of_objects)):
				break


class object_Tree_Handler:
	def __init__(self,filename,maxdepth = 0):
		f = open(filename)
		id_to_level = {}
		if(maxdepth != 0):
			self.maxdepth = maxdepth
			self.objects_per_level = [[] for it in range(0,self.maxdepth)]  
		else:
			self.objects_per_level = [[] for it in range(0,10)] #Assuming max Tree Depth to be 10
			self.maxdepth = 0
		
		for line in f:
			words = line.split(',')
			current_id = eval(words[0])
			parent_id = eval(words[2])
			if(parent_id not in id_to_level):
				id_to_level[parent_id] = -1
			current_level = id_to_level[parent_id] + 1
			id_to_level[current_id] = current_level
			
			self.objects_per_level[current_level].append(words[1])
			if(current_level > self.maxdepth):
				self.maxdepth = current_level

	def setConstants(self,max_TCP_per_domain,max_objects_per_tcp):
		self.maxTCP = max_TCP_per_domain
		self.maxOBJ = max_objects_per_tcp
	
	def getLevelOfTree(self,level):
		domain_map = {}
		for object in self.objects_per_level[level]:
			key = object.split('/')[2]
			if(key not in domain_map):
				domain_map[key] = [object]
			else:
				domain_map[key].append(object)

		thread_list = [] 
		for key in domain_map.keys():
			thread = handle_domain(key,domain_map[key],self.maxTCP,self.maxOBJ)
			thread.start()
			thread_list.append(thread)

		for thread in thread_list:
			thread.join()


	def getTree(self):
		for i in range(0,self.maxdepth):
			self.getLevelOfTree(i)
	

x = object_Tree_Handler('../dumps/www.vox.com.objt')
x.setConstants(2,2)
x.getLevelOfTree(1)


