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
		for idx in range(0,len(self.list_of_objects)):
			request = self.list_of_objects[idx]
			all_data = ''
			#if(idx != len(self.list_of_objects) -1):
			request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\nConnection: keep-alive\r\n\r\n"
			#else:
				#request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain+ "\r\nConnection: close\r\n\r\n"
				#print 'The id for request: ',str(oid)
			connection.send(request_string)
			
			#f = open(request,'w')
			#dir_path = 'dl/' + request.split('//')[1]
			#filemutex.lock(get_filestream,dir_path)
			#filemutex.unlock()
			_oid = 0
			'''with my_lock:
				_oid = oid
				g = open('Mapping.txt','a')
				g.write(str(oid) + '\t' + request.split('//')[1] +'\n')
				f = open('dl/'+str(oid)+'.txt','w')
				oid = oid + 1
				g.close()'''
			f = open('ErrorText2.txt','a')
			flag = False
			while(True):
				try:
					data = connection.recv(1024)
						
				except:
					print 'Bad Request: ', request
					data = ''
				if(len(data) == 0):
					break
				else:
					#f.write(data)
					flag = True
			#print all_data
			if(not flag):
				#print '\n\n'
				with my_lock:
					f.write('\nRequest : ' + request)
					f.write('\nDomain name : ' + self.domain)
					f.write('\nFor the sake of completion: ' + request_string)
				
			'''with your_lock:
				print( str(_oid) + " is done writing\n")'''
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
		file = open('ErrorText2.txt')
		Error_set = set()
		for line in file:
			line = line.split(' : ')
			if(line[0]== 'Request'):
				Error_set.add(line[1].rstrip('\n'))
		
		for item in domain_map.keys():
			print '\nStart: ',item
			counter = 0
			bad_idx_list = []
			for items in domain_map[item]:
				print '\t',items
				if(items in Error_set):
					bad_idx_list.append(counter)
				counter = counter + 1
			print 'Total number of objects: ',str(len(domain_map[item]))
			print 'The Bad Indices are as follows: ',
			for item in bad_idx_list:
				print item,
			print ''
			print 'End'

		'''thread_list = [] 
		for key in domain_map.keys():
			thread = handle_domain(key,domain_map[key],self.maxTCP,self.maxOBJ)
			thread.start()
			thread_list.append(thread)

		for thread in thread_list:
			thread.join()'''


	def getTree(self):
		for i in range(0,self.maxdepth):
			self.getLevelOfTree(i)
	

x = object_Tree_Handler('../dumps/www.vox.com.objt')
x.setConstants(2,2)
x.getLevelOfTree(1)


