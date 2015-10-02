import json
import sys
import os
import urlparse
import re
import csv
from dateutil import parser, relativedelta
import datetime
import pyshark as ps

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

def classify(har_data):
	print "Object Type Classification:\n"
	obj_type_list = {}
	obj_type_list['Images'] = []
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
				elif obj_type == 'image':
					obj_type_list['Images'].append(entry['request']['url'])
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
	for key in obj_type_list.keys():
		if len(obj_type_list[key]) == 0:
			continue
		print key + ":"
		for i,url in enumerate(obj_type_list[key]):
			if len(url) > 70:
				print str(i+1) + ". " + url[:50] + "...." + url[-10:] + "\n"
			else:
				print str(i+1) + ". " + url + "\n"

def print_data(domain_list, domain_info, domain_size):
	for i, domain in enumerate(domain_list):
		print str(i+1) + ". Domain name: " + domain
		print "Total number of objects downloaded: " + str(domain_size[domain][1])
		print "Total size of objects downloaded: " + str(domain_size[domain][0]) + " bytes"
		print "No. of TCP connections opened: " + str(len(domain_info[domain]))
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			print "TCP Connection: " + str(j+1)
			print "No. of objects downloaded: " + str(len(domain_info[domain][connection]))
			total_size = sum([pkt['size'] for pkt in domain_info[domain][connection]])
			print "Size of objects downloaded: " + str(total_size) + " bytes"
			print ""
		print ""

def timing_analysis(har_data, pcap_data, domain_info, domain_list):
	first_request_time = parser.parse(har_data[0]['startedDateTime'])
	last_load_time = max([(parser.parse(entry['startedDateTime']) + datetime.timedelta(microseconds = int(entry['time']) * 1000)) for entry in har_data])
	delta = relativedelta.relativedelta(last_load_time, first_request_time)
	print "Page load time: " + str(delta.minutes) + " minutes, " + str(delta.seconds) + " seconds and " + str(delta.microseconds // 1000) + " milliseconds"
	network_max_goodput = 0
	network_size = 0
	network_receive = 0
	network_time_list = []
	for i, domain in enumerate(domain_list):
		print str(i+1) + ". Domain name: " + domain
		for j, connection in enumerate(sorted(domain_info[domain].keys())):
			connection_id = domain_info[domain][connection]
			for pkt in connection_id:
				if pkt['entry']['timings']['dns'] != 0:
					print "%d.DNS Query Time: %d ms" % (j+1, pkt['entry']['timings']['dns'])
		print "" 
		time_list = []
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
			active_time = connect + wait + receive + send
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
				print "Average Goodput of Connection: %.3f" % average_goodput
				print "Maximum Goodput of Connection: %.3f" % max_goodput
			else:
				print"Goodput not defined as total receiving time = 0"
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

def analyse(har_data, pcap_data):
	n_objects = len(har_data)
	total_size = 0
	domain_info = {}
	domain_size = {}
	domain_list = []
	url_set = set()
	for entry in har_data:
		url_set.add(entry['request']['url'])
	for pkt in pcap_data:
		try:
			if pkt.http.request_method == 'GET':
				if pkt.http.request_full_uri not in url_set:
					continue
				domain = pkt.http.host
				src_port = pkt.tcp.port
				if domain not in domain_info:
					domain_info[domain] = {}
					domain_size[domain] = [0,0]
					domain_list.append(domain)
				if src_port not in domain_info[domain]:
					domain_info[domain][src_port] = []
				domain_info[domain][src_port].append({'url' : pkt.http.request_full_uri})
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
		total_size += size
		if domain in domain_info:
			for connection in domain_info[domain]:
				for pkt in domain_info[domain][connection]:
					if pkt['url'] == url:
						pkt['size'] = size
						pkt['entry'] = entry
						domain_size[domain][0] += size
						domain_size[domain][1] += 1
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
	with open(har_file) as hf:
		har_data = json.load(hf)['log']['entries']
	with open(pcap_file) as pf:
		display_filter = "http && ip.src == "
		display_filter += src_ip
		pcap_data = ps.FileCapture(pcap_file, display_filter = display_filter)
	domain_list, domain_info, domain_size = analyse(har_data, pcap_data)
	#print domain_info
	#print_data(domain_list, domain_info, domain_size)
	#classify(har_data)
	build_download_tree(har_file, domain_info, domain_list)
	build_object_tree(har_file, har_data)
	timing_analysis(har_data, pcap_data, domain_info, domain_list)