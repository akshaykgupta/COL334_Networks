import json
import sys
import os
import urlparse
import re
import csv
from dateutil import parser, relativedelta
import datetime, time
import pyshark as ps
import socket, ssl

def send_get_request(url):
	domain = urlparse.urlparse(url).netloc
	data = ""
	if url.startswith("https://"):
		sock = ssl.wrap_socket(socket.socket(socket.AF_INET , socket.SOCK_STREAM, 0))
		sock.connect((domain,443))
	else:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		sock.connect((domain,80))
	req_str = "GET " + url + " HTTP/1.1\r\nHost: " + domain + "\r\nConnection: close\r\n\r\n"
	sock.send(req_str)
	start = time.time()
	while(True):
		data = sock.recv(1024)
		if len(data)==0 :
			break
	time_taken = time.time() - start
	sock.close()
	return time_taken

def build_object_tree(har_file, har_data):
	object_id = {}
	obj_file = ""
	if har_file.endswith('.har'):
		obj_file = har_file.rstrip('.har')
	else:
		obj_file = har_file
	obj_file += ".objt"
	of = open(obj_file, 'w')
	ofc = csv.writer(of)
	for i, entry in enumerate(har_data):
		url = entry['request']['url']
		object_id[url] = i
		ref_id = i
		for header in entry['request']['headers']:
			if header['name'] == 'Referer' or header['name'] == 'referer':
				ref_id = object_id[header['value']]
		row = []
		row.append(i)
		row.append(url)
		row.append(ref_id)
		ofc.writerow(row)
	of.close()

def print_object_tree(har_data):
	print "Object Tree:\n"
	printed = {}

	def print_descendants(parent_url, level):
		for entry in har_data:
			url = entry['request']['url']
			for header in entry['request']['headers']:
				if header['name'] == 'Referer' or header['name'] == 'referer':
					if header['value'] == parent_url:
						tabs = ''.join(['\t']*level)
						if len(url) > 70:
							print tabs + url[:50] + "...." + url[-10:]
						else:
							print tabs + url
						printed[url] = True
						print_descendants(url, level + 1)
 
	for entry in har_data:
		url = entry['request']['url']
		if url not in printed:
			if len(url) > 70:
				print url[:50] + "...." + url[-10:]
			else:
				print url
			print_descendants(url, 1)

def build_download_tree(har_file, domain_info, domain_list):
	down_file = ""
	if har_file.endswith('.har'):
		down_file = har_file.rstrip('.har')
	else:
		down_file = har_file
	down_file += ".downt"
	df = open(down_file, 'w')
	dfc = csv.writer(df)
	for domain in domain_list:
		for i, connection in enumerate(sorted(domain_info[domain].keys())):
			for pkt in domain_info[domain][connection]:
				row = []
				row.append(domain)
				row.append(i+1)
				row.append(pkt['url'])
				dfc.writerow(row)
	df.close()

def print_download_tree(domain_info, domain_list):
	print "Download Tree:\n"
	for domain in domain_list:
		print "Domain: " + domain
		for i, connection in enumerate(sorted(domain_info[domain].keys())):
			print "TCP Connection: " + str(i+1)
			for pkt in domain_info[domain][connection]:
				if len(pkt['url']) > 70:
					print pkt['url'][:50] + "...." + pkt['url'][-10:]
				else:
					print pkt['url']
			print ""
		print ""

def classify(har_data):
	print "Object Type Classification:\n"
	obj_type_list = {}
	obj_type_list['Other Images'] = []
	obj_type_list['JPEG Images'] = []
	obj_type_list['PNG Images'] = []
	obj_type_list['GIFs'] = []
	obj_type_list['HTML'] = []
	obj_type_list['Javascript'] = []
	obj_type_list['CSS'] = []
	obj_type_list['Fonts'] = []
	obj_type_list['Video'] = []
	obj_type_list['Audio'] = []
	obj_type_list['PDFs'] = []
	obj_type_list['JSON'] = []
	obj_type_list['Flash'] = []
	obj_type_list['Others'] = []
	for entry in har_data:
		for header in entry['response']['headers']:
			if header['name'] == 'Content-Type':
				obj_type = re.split('[, /;]+', header['value'])[0] 
				obj_ext = re.split('[, /;]+', header['value'])[1]
				if obj_ext.find('javascript') != -1:
					obj_type_list['Javascript'].append(entry['request']['url'])
				elif obj_type.find('font') != -1 or obj_ext.find('font') != -1:
					obj_type_list['Fonts'].append(entry['request']['url'])
				elif obj_type == 'image' and obj_ext == 'jpeg':
					obj_type_list['JPEG Images'].append(entry['request']['url'])
				elif obj_type == 'image' and obj_ext == 'png':
					obj_type_list['PNG Images'].append(entry['request']['url'])
				elif obj_type == 'image' and obj_ext == 'gif':
					obj_type_list['GIFs'].append(entry['request']['url'])				
				elif obj_type == 'image':
					obj_type_list['Other Images'].append(entry['request']['url'])
				elif obj_ext == 'css':
					obj_type_list['CSS'].append(entry['request']['url'])
				elif obj_ext == 'html':
					obj_type_list['HTML'].append(entry['request']['url'])
				elif obj_type == 'audio':
					obj_type_list['Audio'].append(entry['request']['url'])
				elif obj_type == 'video':
					obj_type_list['Video'].append(entry['request']['url'])
				elif obj_ext == 'pdf':
					obj_type_list['PDFs'].append(entry['request']['url'])
				elif obj_ext == 'json':
					obj_type_list['JSON'].append(entry['request']['url'])
				elif obj_ext == 'x-shockwave-flash':
					obj_type_list['Flash'].append(entry['request']['url'])
				else:
					obj_type_list['Others'].append(entry['request']['url'])
				break
	for key in sorted(obj_type_list.keys()):
		if len(obj_type_list[key]) == 0:
			continue
		print key + ":"
		for i,url in enumerate(obj_type_list[key]):
			if len(url) > 70:
				print str(i+1) + ". " + url[:50] + "...." + url[-10:] + "\n"
			else:
				print str(i+1) + ". " + url + "\n"

def print_data(domain_list, domain_info, domain_size):
	total_tcp_connections = 0
	for i, domain in enumerate(domain_list):
		print str(i+1) + ". Domain name: " + domain
		print "Total number of objects downloaded: " + str(domain_size[domain][1])
		print "Total size of objects downloaded: " + str(domain_size[domain][0]) + " bytes"
		print "No. of TCP connections opened: " + str(len(domain_info[domain])) + "\n"
		total_tcp_connections += len(domain_info[domain])
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			print "TCP Connection: " + str(j+1)
			print "No. of objects downloaded: " + str(len(domain_info[domain][connection]))
			total_size = sum([pkt['size'] for pkt in domain_info[domain][connection] if 'size' in pkt])
			print "Size of objects downloaded: " + str(total_size) + " bytes"
			print ""
		print ""

def max_goodput_calculation(goodput_list, domain_list, domain_info, domain_size):
	a = []
	print "\nTheoretical Calculation of page load time assuming maximum goodput for each domain on a single TCP connection: "
	for i, domain in enumerate(domain_list):
		total_size = str(domain_size[domain][0])
		goodput = goodput_list[i]
		print domain + " - Total object size: " + str(total_size) + ", Max. goodput: " + str(goodput)
		if float(goodput) != 0.0:
			a.append(float(total_size)/float(goodput))
	print "\nCalculated page load time: " + str(max(a)) + " ms"

def collapse_objects_calculation(har_data, domain_list, domain_info):
	original_active_time = {}
	new_active_time = {}
	connection_map = {}
	level = {}
	for i, entry in enumerate(har_data):
		url = entry['request']['url']
		level[url] = 0
		for header in entry['request']['headers']:
			if header['name'] == 'Referer' or header['name'] == 'referer':
				level[url] = level[header['value']] + 1

	for i, domain in enumerate(domain_list):
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			connection_id = domain_info[domain][connection]
			connect = sum([pkt['entry']['timings']['connect'] for pkt in connection_id])
			dns = sum([pkt['entry']['timings']['dns'] for pkt in connection_id])
			receive = max([pkt['entry']['timings']['receive'] for pkt in connection_id])
			original_active_time[connection] = dns + connect + receive
			for pkt in domain_info[domain][connection]:
				connection_map[pkt['url']] = connection
	parent = {}
	levels = {}
	for i in range(10):
		levels[i] = []
	for i, domain in enumerate(domain_list):
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			max_level = 0
			for pkt in domain_info[domain][connection]:
				for header in pkt['entry']['request']['headers']:
					if header['name'] == 'Referer' or header['name'] == 'referer':
						if max_level < level[pkt['url']]:
							max_level = level[pkt['url']]
							par_connection = connection_map[header['value']]
			levels[max_level].append((connection, par_connection))
	for lvl in range(9, -1, -1):
		for connection in levels[lvl]:
			if connection[1] not in new_active_time:
				new_active_time[connection[1]] = original_active_time[connection[1]] + original_active_time[connection[0]]
			else:
				if original_active_time[connection[1]] + original_active_time[connection[0]] > new_active_time[connection[1]]:
					new_active_time[connection[1]] = original_active_time[connection[1]] + original_active_time[connection[0]]
	calc_time = max([new_active_time[connection] for connection in levels[0]])
	print "\nCalculated time if TCP connections can collapse on get requests: " + str(calc_time)

def create_timeline(har_data, domain_info, domain_list):
	f = open("../doc/timing_info.csv", 'wb')
	c = csv.writer(f)
	g = open("../doc/timeline.csv", 'wb')
	d = csv.writer(g)
	start = parser.parse(har_data[0]['startedDateTime'])
	end = max([(parser.parse(entry['startedDateTime']) + datetime.timedelta(microseconds = int(entry['time']) * 1000)) for entry in har_data])
	interval = start - end
	interval = interval.seconds + float(interval.microseconds / 1000000)
	for i, domain in enumerate(domain_list):
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			row1 = []
			connection_id = domain_info[domain][connection]
			first_request_time = parser.parse(connection_id[0]['entry']['startedDateTime']) + datetime.timedelta(microseconds = (connection_id[0]['entry']['timings']['blocked'] + connection_id[0]['entry']['timings']['dns']) * 1000)
			last_load_time = max([(parser.parse(entry['entry']['startedDateTime']) + datetime.timedelta(microseconds = entry['entry']['time'] * 1000)) for entry in connection_id])			
			total_wait_time = first_request_time - start
			total_active_time = last_load_time - first_request_time
			total_wait_time = total_wait_time.seconds + (float(total_wait_time.microseconds) / 1000000)
			total_active_time = total_active_time.seconds + (float(total_active_time.microseconds) / 100000)
			row1.append(domain + ": Conn " + str(j+1))
			row1.append(total_wait_time)
			row1.append(total_active_time)
			d.writerow(row1)
			for pkt in domain_info[domain][connection]:
				row = []
				if len(pkt['url']) <= 34:
					url = pkt['url']
				else:
					url = pkt['url'][:20] + '....' + pkt['url'][-10:]
				row.append(url)
				wait_time = parser.parse(pkt['entry']['startedDateTime']) - start
				wait_time = (wait_time.seconds) + float(wait_time.microseconds / 1000)
				row.append(wait_time / interval)
				row.append((float(pkt['entry']['timings']['blocked'])/1000) / interval)
				row.append((float(pkt['entry']['timings']['dns'])/1000) / interval)
				row.append((float(pkt['entry']['timings']['connect'])/1000) / interval)
				row.append((float(pkt['entry']['timings']['send'])/1000) / interval)
				row.append((float(pkt['entry']['timings']['wait'])/1000) / interval)
				row.append((float(pkt['entry']['timings']['receive'])/1000) / interval)
				c.writerow(row)

def timing_analysis(har_data, pcap_data, domain_info, domain_list, compare = 'False'):
	first_request_time = parser.parse(har_data[0]['startedDateTime'])
	last_load_time = max([(parser.parse(entry['startedDateTime']) + datetime.timedelta(microseconds = int(entry['time']) * 1000)) for entry in har_data])
	delta = relativedelta.relativedelta(last_load_time, first_request_time)
	print "Timing Information:"
	print "Page load time: " + str(delta.minutes) + " minutes, " + str(delta.seconds) + " seconds and " + str(delta.microseconds // 1000) + " milliseconds\n"
	network_max_goodput = 0
	network_size = 0
	network_receive = 0
	network_time_list = []
	goodput_list = []
	# f = open("../doc/goodputs.csv", 'wb')
	# c = csv.writer(f)
	for i, domain in enumerate(domain_list):
		dns_query = False
		print str(i+1) + ". Domain name: " + domain
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			connection_id = domain_info[domain][connection]
			for pkt in connection_id:
				if pkt['entry']['timings']['dns'] != 0:
					dns_query = True
					print "DNS Query Time: %d ms (On connection %d)" % (pkt['entry']['timings']['dns'], j+1)
		if dns_query is False:
			print "DNS Query Time: 0 ms"
		print "" 
		time_list = []
		domain_goodput = -1.0
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			connection_id = domain_info[domain][connection]
			print "TCP Connection: " + str(j+1)
			connect = sum([pkt['entry']['timings']['connect'] for pkt in connection_id])
			wait = sum([pkt['entry']['timings']['wait'] for pkt in connection_id])
			receive = sum([pkt['entry']['timings']['receive'] for pkt in connection_id])
			send = sum([pkt['entry']['timings']['send'] for pkt in connection_id])
			print "Connection Establishment Time: " + str(connect)
			print "Waiting Time: " + str(wait)
			print "Receiving Time: " + str(receive)
			print "Sending Time: " + str(send)
			first_request_time = parser.parse(connection_id[0]['entry']['startedDateTime']) + datetime.timedelta(microseconds = (connection_id[0]['entry']['timings']['blocked'] + connection_id[0]['entry']['timings']['dns']) * 1000)
			last_load_time = max([(parser.parse(entry['entry']['startedDateTime']) + datetime.timedelta(microseconds = entry['entry']['time'] * 1000)) for entry in connection_id])
			delta = relativedelta.relativedelta(last_load_time, first_request_time)
			time_list.append((first_request_time, '+'))
			time_list.append((last_load_time, '-'))
			print "Time for which connection was active: %d minutes, %d seconds and %d milliseconds" % (delta.minutes, delta.seconds, delta.microseconds // 1000)
			total_active_time = delta.minutes * 60 * 1000 + delta.seconds * 1000 + delta.microseconds // 1000
			active_time = wait + receive + send
			active_percentage = float(active_time) / float(total_active_time)
			idle_percentage = 1.0 - active_percentage
			print "Percentage of Time Active: %.3f" % active_percentage
			print "Percentage of Time Idle: %.3f" % idle_percentage
			total_size = sum([pkt['size'] for pkt in connection_id])
			network_size += total_size
			network_receive += receive
			if receive != 0:
				average_goodput = float(total_size) / float(receive)
				max_size = 0
				largest_object = connection_id[0]
				for pkt in connection_id:
					if pkt['size'] > max_size and pkt['entry']['timings']['receive'] != 0:
						max_size = pkt['size']
						largest_object = pkt
				max_goodput = float(largest_object['size']) / float(largest_object['entry']['timings']['receive'])
				if network_max_goodput < max_goodput:
					network_max_goodput = max_goodput
				if domain_goodput < max_goodput:
					domain_goodput = max_goodput
				print "Average Goodput of Connection: %.3f" % average_goodput
				print "Maximum Goodput of Connection: %.3f" % max_goodput
				# row = []
				# row.append(domain + ": Conn " + str(j+1))
				# row.append(average_goodput)
				# row.append(max_goodput)
				# c.writerow(row)
			else:
				print"Goodput not defined as total receiving time = 0"
			if compare == 'True':
				print "Maximum Goodput through direct request: " + str(float(largest_object['size'])/float(send_get_request(largest_object['url']) * 1000))
			print ""
		max_connections = 0
		connections = 0
		for time in sorted(time_list, key = lambda t: t[0]):
			if time[1] == '+':
				connections += 1
			else:
				if connections > max_connections:
					max_connections = connections
				connections -= 1
		print "Maximum No. of TCP connections open simultaneously: %d \n" % max_connections
		print ""
		network_time_list.extend(time_list)
		goodput_list.append(max_goodput)
	max_connections = 0
	connections = 0
	for time in sorted(network_time_list, key = lambda t: t[0]):
		if time[1] == '+':
			connections += 1
		else:
			if connections > max_connections:
				max_connections = connections
			connections -= 1
	print "Maximum No. of TCP connections open simultaneously in entire network: %d" % max_connections
	network_avg_goodput = float(network_size) / float(network_receive)
	print "Average Goodput of Network: %.3f" % network_avg_goodput
	print "Maximmum Goodput of Network: %.3f" % network_max_goodput
	return goodput_list

def analyse(har_data, pcap_data):
	n_objects = 0
	total_size = 0
	domain_info = {}
	domain_size = {}
	domain_list = []
	matched = {}
	for entry in har_data:
		if entry['request']['url'] not in matched:
			matched[entry['request']['url']] = 1
		else:
			matched[entry['request']['url']] += 1
	for pkt in pcap_data:
		try:
			if pkt.http.request_method == 'GET':
				if pkt.http.request_full_uri not in matched:
					continue
				if matched[pkt.http.request_full_uri] == 0:
					continue
				matched[pkt.http.request_full_uri] -= 1
				domain = pkt.http.host
				src_port = pkt.tcp.port
				if domain not in domain_info:
					domain_info[domain] = {}
					domain_size[domain] = [0,0]
					domain_list.append(domain)
				if src_port not in domain_info[domain]:
					domain_info[domain][src_port] = []
				domain_info[domain][src_port].append({'url' : pkt.http.request_full_uri, 'matched' : False})
		except:
			pass
	for entry in har_data:
		url = entry['request']['url']
		for header in entry['response']['headers']:
			if header['name'] == 'Content-Length':
				size = int(header['value'])
		domain = urlparse.urlparse(url).netloc
		try:
			size = size
		except:
			size = entry['response']['bodySize']
		matched = False
		if domain in domain_info:
			for connection in domain_info[domain]:
				for pkt in domain_info[domain][connection]:
					if pkt['url'] == url and not pkt['matched']:
						pkt['size'] = size
						pkt['entry'] = entry
						domain_size[domain][0] += size
						domain_size[domain][1] += 1
						pkt['matched'] = True
						matched = True
						total_size += size
						n_objects += 1
						break
				if matched:
					break

	print "Total No. of objects downloaded: " + str(n_objects)
	print "Total size of objects downloaded: " + str(total_size) + " bytes\n"
	return domain_list, domain_info, domain_size

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print "Require three arguments : HAR File, PCAP File and host IP"
		exit()
	elif len(sys.argv) > 3:
		har_file = sys.argv[1]
		pcap_file = sys.argv[2]
		src_ip = sys.argv[3]
	if len(sys.argv) == 5:
		compare = sys.argv[4]
	else:
		compare = "False"
	with open(har_file) as hf:
		har_data = json.load(hf)['log']['entries']
	with open(pcap_file) as pf:
		display_filter = "http && ip.src == "
		display_filter += src_ip
		pcap_data = ps.FileCapture(pcap_file, display_filter = display_filter)
	domain_list, domain_info, domain_size = analyse(har_data, pcap_data)
	#print domain_info
	#create_timeline(har_data, domain_info, domain_list)
	print_data(domain_list, domain_info, domain_size)
	classify(har_data)
	print ""
	print_object_tree(har_data)
	print "\n"
	print_download_tree(domain_info, domain_list)
	build_download_tree(har_file, domain_info, domain_list)
	build_object_tree(har_file, har_data)
	goodput_list = timing_analysis(har_data, pcap_data, domain_info, domain_list, compare)
	# max_goodput_calculation(goodput_list, domain_list, domain_info, domain_size)
	collapse_objects_calculation(har_data, domain_list, domain_info)