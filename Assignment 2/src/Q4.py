import sys, socket, json, time, thread, threading, os, mutex

filemutex = mutex.mutex()

def get_filestream( fullpath ):
	directory = os.path.dirname(filename) #Will not having a directory part create a problem? Like, will directory = "" create problems?
	if not os.path.exists(directory):
		filemutex.lock(os.makedirs , directory)
		filemutex.unlock()
	f = open(fullpath)
	return f

class handle_objects(threading.Thread):
	def __init__(self,domain_name,list_of_objects):
		threading.Thread.__init__(self)
		self.domain = domain_name
		self.list_of_objects = list_of_objects

	def run(self):
		#TODO: Pretty Printing.
		connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
		connection.connect((self.domain,80))
		for idx in range(0,len(self.list_of_objects)):
			request = self.list_of_objects[idx]
			all_data = ''
			if(idx != len(self.list_of_objects) -1):
				request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\n\r\n"
			else:
				request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\nConnection: close\r\n\r\n"
			connection.send(request_string)
			#f = open(request,'w')
			while(True):
				data = connection.recv(1024)
				if(len(data) == 0):
					break
				else:
					all_data = all_data + data 
			f = get_filestream(request)
			#print all_data
			f.write(all_data)
			f.close()
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


