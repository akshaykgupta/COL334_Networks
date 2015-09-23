import sys, socket, json, time, thread, threading

class handle_objects(threading.Thread):
	def __init__(self,domain_name,list_of_objects):
		self.domain = domain_name
		self.list_of_objects = list_of_objects

	def run(self):
		#TODO: Parallelise The object download.
		connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
		connection.connect((self.domain,80))
		for request in self.list_of_objects:
			all_data = ''
			request_string = "GET " + request + " HTTP/1.1\r\n\r\n"
			connection.send(request_string)
			while(True):
				data = connection.recv(1024)
				if(len(data) == 0):
					break
				else:
					all_data = all_data + data 

			#Store all_data somewhere.

class handle_domain(threading.Thread):
	def __init__(self,domain_name,list_of_objects,maxTCP,maxOBJ):
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
				if(high > len(list_of_objects)):
					high = len(list_of_objects)
				thread = handle_objects(self.domain,self.list_of_objects[low:high])
				thread.start()
				thread_list.append(thread)
				low = high
				if(len(list_of_objects) == low):
					break
			#So that only maxTCP connections are active at any given time.
			for thread in thread_list:
				thread.join()
			if(low == len(list_of_objects)):
				break


class object_Tree_Handler:
	def __init__(self,filename,maxdepth = 0):
		f = open(filename)
		if(maxdepth != 0):
			self.maxdepth = maxdepth
			self.objects_per_level = [[] for it in range(0,self.maxdepth)]  
		else:
			self.objects_per_level = [[] for it in range(0,10)] #Assuming max Tree Depth to be 10
			self.maxdepth = 0
		for line in f:
			words = line.split()
			self.objects_per_level[eval(words[0])].append(words[1])
			if(eval(words[0]) > self.maxdepth):
				self.maxdepth = eval(words[0])

	def setConstants(max_TCP_per_domain,max_objects_per_tcp):
		self.maxTCP = max_TCP_per_domain
		self.maxOBJ = max_objects_per_tcp
	
	def getLevelOfTree(self,level):
		domain_map = {}
		for object in self.objects_per_level[level]:
			key = object.lstrip('http://').split('/')[0]
			if(key not in domain_map):
				domain_map[key] = [object]
			else:
				domain_map[key].append(object)
		thread_list = [] 
		for key domain_map.keys():
			thread = handle_domain(key,domain_map[key],self.maxTCP,self.maxOBJ)
			thread.start()
			thread_list.append(thread)

		for thread in thread_list:
			thread.join()


	def getTree(self):
		for i in range(0,self.maxdepth):
			self.getLevelOfTree(i)
	


