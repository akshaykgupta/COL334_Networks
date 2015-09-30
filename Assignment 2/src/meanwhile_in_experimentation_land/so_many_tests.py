import socket
requests = []

requests.append('www.google-analytics.com/analytics.js')
requests.append('www.google-analytics.com/r/collect?v=1&_v=j38&a=113547862&t=pageview&_s=1&dl=http%3A%2F%2Fwww.vox.com%2Fa%2Fmaps-explain-the-middle-east&ul=en-us&de=UTF-8&dt=40%20maps%20that%20explain%20the%20Middle%20East&sd=24-bit&sr=1366x768&vp=1349x282&je=0&fl=16.0%20r0&_u=AACAAEABI~&jid=373540455&cid=1179577113.1435504289&tid=UA-48698701-1&_r=1&cd1=%2Fa%2Fmaps-explain-the-middle-east&cd2=Editorial%20App%20%E2%80%93%20list&cd3=app&cd4=Max%20Fisher&cd5=2014-05-05%2008%3A00&z=1974706444')
#requests.append('b.scorecardresearch.com/b2?c1=2&c2=7976662&ns__t=1442243534030&ns_c=UTF-8&c8=40%20maps%20that%20explain%20the%20Middle%20East&c7=http%3A%2F%2Fwww.vox.com%2Fa%2Fmaps-explain-the-middle-east&c9=')
#requests.append('ping.chartbeat.net/ping?h=vox.com&p=%2Fa%2Fmaps-explain-the-middle-east&u=BClAvKDyLZf8DvB4Ww&d=vox.com&g=2724&n=0&f=f0001&c=1&x=22283&m=22283&y=22731&o=1349&w=282&j=30&R=1&W=0&I=0&E=10&e=5&r=&t=BCFttRCiGGyodBR0pdsSyORY7n&V=65&tz=-330&sn=4&_')

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
sock.connect(('google-analytics.com',80))
filenames = []
for idx in range(0,len(requests)):
	request = requests[idx]
	request_string = ''
	if(idx != len(requests) -1):
		request_string = "GET " + request + " HTTP/1.1\r\nHost: " + "google-analytics.com"+ "\r\nConnection: keep-alive\r\n\r\n"
	else:
		request_string = "GET " + request + " HTTP/1.1\r\nHost: " + "google-analytics.com"+ "\r\nConnection: keep-alive\r\n\r\n"
	sock.send(request_string)
	filename = request.split('/')
	filename = filename[len(filename) - 1]
	filenames.append(filename[len(filename)-5:len(filename)])
counter = -1
f = None
num_objects = 3
residual_data = ''
all_data = ''
fileNumber = 0
print 'Reached Here'
data = sock.recv(1024)
while(len(data)!=0):
	all_data = all_data + data
	try:
		sock.settimeout(5.0)
		data = sock.recv(1024)
		sock.settimeout(None)
	except:
		data = ''
print 'Reached Here'
f = open('Input2.txt','w')
f.write(all_data)
f.close()
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
	print 'Here'
	counter = -1
	f = open(filenames[fileNumber],'w')
	print length_of_file
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
	f = open(filenames[fileNumber],'w')
	fileNumber = fileNumber + 1




