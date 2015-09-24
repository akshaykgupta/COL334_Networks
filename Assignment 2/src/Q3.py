import json
import sys
import os
import urlparse
import re
import csv
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
	obj_type_list = {}
	obj_type_list['Images'] = []
	obj_type_list['HTML'] = []
	obj_type_list['Javascript'] = []
	obj_type_list['CSS'] = []
	obj_type_list['Fonts'] = []
	obj_type_list['Video'] = []
	obj_type_list['Audio'] = []
	obj_type_list['PDFs'] = []
	obj_type_list['Others'] = []
	for entry in har_data:
		for header in entry['response']['headers']:
			if header['name'] == 'Content-Type':
				obj_type = re.split('[, /;]+', header['value'])[0] 
				obj_ext = re.split('[, /;]+', header['value'])[1]
				if obj_ext.find('javascript') != -1:
					obj_type_list['Javascript'].append(entry['request']['url'])
				if obj_type.find('font') != -1 or obj_ext.find('font') != -1:
					obj_type_list['Fonts'].append(entry['request']['url'])
				if obj_type == 'image':
					obj_type_list['Images'].append(entry['request']['url'])
				if obj_ext == 'css':
					obj_type_list['CSS'].append(entry['request']['url'])
				if obj_ext == 'html':
					obj_type_list['HTML'].append(entry['request']['url'])
				if obj_type == 'audio':
					obj_type_list['Audio'].append(entry['request']['url'])
				if obj_type == 'video':
					obj_type_list['Video'].append(entry['request']['url'])
				if obj_ext == 'pdf':
					obj_type_list['PDFs'].append(entry['request']['url'])
				else:
					obj_type_list['Others'].append(entry['request']['url'])
				break
	for key in obj_type_list.keys():
		if len(obj_type_list[key]) == 0:
			continue
		print key + ":"
		for i,url in enumerate(obj_type_list[key]):
			print str(i+1) + ". " + url + "\n"

def print_data(domain_info):
	pass

def analyse(har_data, pcap_data):
	n_objects = len(har_data)
	total_size = 0
	domain_info = {}
	domain_size = {}
	domain_list = []
	for pkt in pcap_data:
		try:
			if pkt.http.request_method == 'GET':
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
		size = entry['response']['content']['size']
		dns = entry['timings']['dns']
		connect = entry['timings']['connect']
		wait = entry['timings']['wait']
		receive = entry['timings']['receive']
		send = entry['timings']['send']
		domain = urlparse.urlparse(url).netloc
		total_size += size
		if domain in domain_info:
			for connection in domain_info[domain]:
				for pkt in domain_info[domain][connection]:
					if pkt['url'] == url:
						pkt['size'] = size
						pkt['dns'] = dns
						pkt['connect'] = connect
						pkt['wait'] = wait
						pkt['receive'] = receive
						pkt['send'] = send
						domain_size[domain][0] += size
						domain_size[domain][1] += 1
	print "Total No. of objects downloaded: " + str(n_objects)
	print "Total size of objects downloaded: " + str(total_size) + " bytes"
	return domain_list, domain_info, domain_size

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Require two arguments : HAR File and PCAP File"
		exit()
	elif len(sys.argv) > 2:
		har_file = sys.argv[1]
		pcap_file = sys.argv[2]
	with open(har_file) as hf:
		har_data = json.load(hf)['log']['entries']
	with open(pcap_file) as pf:
		pcap_data = ps.FileCapture(pcap_file, display_filter = "http && ip.src == 192.168.0.4")
	domain_list, domain_info, domain_size = analyse(har_data, pcap_data)
	#print_data(domain_info)
	classify(har_data)
	build_download_tree(har_file, domain_info, domain_list)
	build_object_tree(har_file, har_data)