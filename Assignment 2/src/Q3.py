import json
import sys
import os
import urlparse
import pyshark

if len(sys.argv < 3):
	print "Require two arguments : HAR File and PCAP File"
elif len(sys.argv > 2):
	har_file = sys.argv[1]
	pcap_file = sys.argv[2]

with open(har_file) as hf:
	data = json.load(hf)

n_objects = len(data['log']['entries'])
