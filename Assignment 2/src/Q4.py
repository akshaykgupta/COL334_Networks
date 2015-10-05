import socket,threading,sys,json,os,ssl
import Q3 as converter
class downloader:
	#Defining Static Variables
	my_lock = threading.Lock()
	jdx = 0
	index_file = 'Mapping.txt'
	directory_name = 'dl'
	def __init__(self):
		downloader.jdx = 0
		downloader.index_file = 'Mapping.txt'
		downloader.directory_name = 'dl'
	
	def set_constants(self,index_filename,directory):
		if(index_filename != ''):
			downloader.index_file = index_filename
		if(directory != ''):
			downloader.directory_name = directory
	
	
	class handle_connection(threading.Thread):
		def __init__(self,domain,domain_list,flag):
			threading.Thread.__init__(self)
			self.domain = domain
			self.domain_list = domain_list
			self.flag = flag

		def handle_data(self,all_data,filenames):
			fileNumber = 0
			while(len(all_data)!=0):
				length_of_file = -1	
				all_data = all_data.split('\n')
				counter = -1
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
				f = open(downloader.directory_name + '/' +str(filenames[fileNumber]) +'.txt','w')
				if(length_of_file == -1):
					# The very special case of no Content-length
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
			while(fileNumber < len(filenames)):
				f = open(downloader.directory_name + '/' +str(filenames[fileNumber]) +'.txt','w')
				fileNumber = fileNumber + 1
		
		def get_data(self,sock):
			all_data = ''
			try:
				sock.settimeout(60.0)
				data = sock.recv(1024)
				sock.settimeout(None)
			except:
				data = ''
			while(len(data)!=0):
				all_data = all_data + data
				try:
					sock.settimeout(60.0)
					data = sock.recv(1024)
					sock.settimeout(None)
				except:
					data = ''
			return all_data	
		
		def run(self):
			sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
			try:
				sock.connect((self.domain,80))
			except:
				print "Could not connect to domain. ",self.domain
				return

			filenames = []
			https_requests = []
			f = open(downloader.index_file,'a')
			for idx in range(0,len(self.domain_list)):
				request = self.domain_list[idx]
				if(request.startswith('https://')):
					https_requests.append(request)
					continue
				request_string = ''
				if(idx != len(self.domain_list) -1):
					request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain + "\r\nConnection: keep-alive\r\n\r\n"
				else:
					request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain + "\r\nConnection: close\r\n\r\n"
				sock.send(request_string)
				with downloader.my_lock:
					f.write(str(downloader.jdx) + ' ' + request + '\n')
					filenames.append(downloader.jdx)
					downloader.jdx = downloader.jdx + 1
			f.close()
			
			all_data = self.get_data(sock)

			self.handle_data(all_data,filenames)
			sock.close()
			if(not https_requests == []):
				ssl_wrapper = ssl.wrap_socket(socket.socket(socket.AF_INET,socket.SOCK_STREAM,0))
				try:
					ssl_wrapper.connect((self.domain,443))
				except:
					print "Could not connect to domain. ",self.domain
					return
				filenames = []
				f = open(downloader.index_file,'a')
				for idx in range(0,len(https_requests)):
					request = https_requests[idx]
					request_string = ''
					if(idx != len(https_requests) -1):
						request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain + "\r\nConnection: keep-alive\r\n\r\n"
					else:
						request_string = "GET " + request + " HTTP/1.1\r\nHost: " + self.domain + "\r\nConnection: close\r\n\r\n"
					ssl_wrapper.send(request_string)
					with downloader.my_lock:
						f.write(str(downloader.jdx) + ' ' + request + '\n')
						filenames.append(downloader.jdx)
						downloader.jdx = downloader.jdx + 1
				f.close()
				all_data = self.get_data(ssl_wrapper)
				self.handle_data(all_data,filenames)
				ssl_wrapper.close()
			
			

	class distribute_connections(threading.Thread):
		def __init__(self,domain,domain_list,max_TCP,max_OBJ,flag):
			threading.Thread.__init__(self)
			self.domain = domain
			self.domain_list = domain_list
			self.k = max_TCP
			self.t = max_OBJ
			self.flag = flag
		
		def run(self):
			low = 0
			while(True):
				thread_list = []
				for i in xrange(0,self.k):
					high = low + self.t
					if(high > len(self.domain_list)):
						high = len(self.domain_list)
					thread = downloader.handle_connection(self.domain,self.domain_list[low:high],self.flag)
					thread.start()
					thread_list.append(thread)
					low = high
					if(low == len(self.domain_list)):
						break

				for thread in thread_list:
					thread.join()
				if(low == len(self.domain_list)):
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
				words = ['' , '', '']
				_words = line.split(',')
				words[0] = _words[0]
				words[2] = _words[len(_words) - 1]
				words[1] = ','.join(_words[1:len(_words) - 1])
				current_id = eval(words[0])
				parent_id = eval(words[2])
				if(parent_id not in id_to_level):
					id_to_level[parent_id] = -1
				current_level = id_to_level[parent_id] + 1
				id_to_level[current_id] = current_level
				
				self.objects_per_level[current_level].append(words[1])
				if(current_level > self.maxdepth):
					self.maxdepth = current_level

		def set_max_values(self,max_TCP,max_OBJ):
			self.maxTCP = max_TCP
			self.maxOBJ = max_OBJ

		def get_level_of_tree(self,level):
			requests = self.objects_per_level[level]
			domain_map = {}
			http_requests = set()
			for item in requests:
				_itemlist = item.split('//')
				protocol = _itemlist[0]
				url = '//'.join(_itemlist[1:]) 
				domain_name = url.split('/')[0]
				if(not domain_name in domain_map):
					domain_map[domain_name] = [item]
					directory = downloader.directory_name + "/" + domain_name
					if(not os.path.exists(directory)):
						os.makedirs(directory) #Make the domain in which to put it.
				else:
					domain_map[domain_name].append(item)
				protocol = protocol.rstrip(':')
				if(protocol == 'http'):
					http_requests.add(domain_name)

			thread_list = []
			for domain in domain_map:
				if(domain in http_requests):
					thread = downloader.distribute_connections(domain,domain_map[domain],self.maxTCP,self.maxOBJ,True)
				else:
					thread = downloader.distribute_connections(domain,domain_map[domain],self.maxTCP,self.maxOBJ,False)
				thread.start()
				thread_list.append(thread)
			
			for thread in thread_list:
				thread.join()

		def get_tree(self):
			for i in range(0,self.maxdepth+1):
				self.get_level_of_tree(i)

		def post_process(self):
			#ASSERT : The directories exist.
			f = open(downloader.index_file,"r")
			for line in f:
				idx = eval(line.split(" ")[0])
				present_file_name = downloader.directory_name + "/" + str(idx) + ".txt"
				url = line.split(" ")[1]
				domain_name = url.split("//")[1].split("/")[0]
				# extension = url.split(".")[len(url.split(".")) - 1] #Last index.
				# if extension == ".png" or  extension == ".jpg" or extension==".html" or extension==".css" or extension==".js":
				# 	pass
				# else:
				# 	extension = ".txt"
				extension = ".txt"
				new_file_name = downloader.directory_name + "/" + domain_name + "/" + str(idx) + extension
				os.rename(present_file_name,new_file_name) #Rename the file!
			f.close()

if __name__ == '__main__':
	if(len(sys.argv) < 4):
		print 'Improperly Formed request'
		exit()
	else:
		the_downloader = downloader()
		index_file = ''
		directory_name = ''
		if(len(sys.argv) == 5 or len(sys.argv) == 6):
			index_file = sys.argv[4]
			if(len(sys.argv) == 6):
				directory_name = sys.argv[5]
		the_downloader.set_constants(index_file,directory_name)
		if(sys.argv[1].endswith('.har')):
			# What is har_data ?
			with open(sys.argv[1]) as hf:
				har_data = json.load(hf)['log']['entries']
			converter.build_object_tree(sys.argv[1] + '.objt',har_data)
			# Change index_file to whatever you like
			object_file = sys.argv[1].rstrip('.har')
			x = the_downloader.object_Tree_Handler(object_file + '.objt')
			x.set_max_values(eval(sys.argv[2]),eval(sys.argv[3]))
			x.get_tree()
			x.post_process()
		elif(sys.argv[1].endswith('.objt')):
			#Change index_file to whatever you like
			x = the_downloader.object_Tree_Handler(sys.argv[1])
			x.set_max_values(eval(sys.argv[2]),eval(sys.argv[3]))
			x.get_tree()
			x.post_process()
		else:
			print 'Invalid File type entered. Only HAR and OBJ_Trees allowed'

