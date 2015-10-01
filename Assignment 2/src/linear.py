import socket
requests = []
jdx = 0
def handle_domain(domain,domain_list,flag=True):
	global jdx
	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
	if(flag):
		sock.connect((domain,80))
	else:
		sock.connect((domain,443))
	start = jdx
	f = open('Mapping.txt','a')
	for idx in range(0,len(domain_list)):
		request = domain_list[idx]
		request_string = ''
		if(idx != len(requests) -1):
			request_string = "GET " + request + " HTTP/1.1\r\nHost: " + domain + "\r\nConnection: keep-alive\r\n\r\n"
		else:
			request_string = "GET " + request + " HTTP/1.1\r\nHost: " + domain + "\r\nConnection: close\r\n\r\n"
		sock.send(request_string)
		f.write(str(jdx) + ' ' + request + '\n')
		jdx = jdx + 1
	end = jdx
	f.close()
	all_data = ''
	try:
		sock.settimeout(2.0)
		data = sock.recv(1024)
		sock.settimeout(None)
	except:
		data = ''
	while(len(data)!=0):
		all_data = all_data + data
		try:
			sock.settimeout(2.0)
			data = sock.recv(1024)
			sock.settimeout(None)
		except:
			data = ''
	fileNumber = start
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
		f = open('dl/'+str(fileNumber) +'.txt','w')
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
	while(fileNumber < end):
		f = open('dl/'+str(fileNumber) +'.txt','w')
		fileNumber = fileNumber + 1

inputfile = open('www.vox.com.objt')
requests = []
for line in inputfile:
	line = line.split(',')
	if(line[2].rstrip('\r\n') == '0'):
		requests.append(line[1])
domain_map = {}
http_requests = set()
for item in requests:
	[protocol,url] = item.split('//')
	domain_name = url.split('/')[0]
	if(not domain_name in domain_map):
		domain_map[domain_name] = [item]
	else:
		domain_map[domain_name].append(item)
	protocol = protocol.rstrip(':')
	if(protocol == 'http'):
		http_requests.add(domain_name)

for domain in domain_map:
	if(domain in http_requests):
		handle_domain(domain,domain_map[domain],True)
	else:
		handle_domain(domain,domain_map[domain],False)




