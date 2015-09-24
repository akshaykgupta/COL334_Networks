import json
import sys
import os
import urlparse
import csv
import pyshark as ps

def build_object_tree(har_file, har_data):
	object_id = {}
	obj_file = ""
	if har_file.endswith('.har'):
		obj_file = har_file[:-4]
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
				print "Found"
		row = []
		row.append(i)
		row.append(url)
		row.append(ref_id)
		ofc.writerow(row)

def analyse(har_data, pcap_data):
	n_objects = len(har_data)
	print "Total No. of objects downloaded: " + str(n_objects)
	domain_info = {}
	for entry in har_data:
		url = entry['request']['url']
		domain = urlparse.urlparse(url).netloc
		if domain in domain_info:
			domain_info[domain].append(entry)
		else:
			domain_info[domain] = []
			domain_info[domain].append(entry)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Require two arguments : HAR File and PCAP File"
	elif len(sys.argv) > 2:
		har_file = sys.argv[1]
		pcap_file = sys.argv[2]
	with open(har_file) as hf:
		har_data = json.load(hf)['log']['entries']
	with open(pcap_file) as pf:
		pcap_data = ps.FileCapture(pcap_file)
	analyse(har_data, pcap_data)
	build_object_tree(har_file, har_data)