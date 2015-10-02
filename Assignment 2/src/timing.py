import os,Q4,sys
from sys import platform as operating_system

#Edit these:
max_tcp = 8
max_obj = 8 
f = open("timing_analysis.data" , "a")

for tcp in range(1,max_tcp):
	for obj in range(1,max_obj):

		FLUSH DNS # IMPORTANT !!!!!!!! USE SYSTEM KA FLUSH DNS
		if operating_system == "linux":
			#TODO
		else if operating_system == "win32":
			os.system("ipconfig /flushdns")
		else if operating_system == "darwin":
			#TODO
		Q4.index_file = "mapping_for_" + str(tcp) + "_" + str(obj) + ".txt"
		Q4.directory_name = "dl_" + str(tcp) + "_" + str(obj)
		#START TIME
		start = time.time()
		x = object_Tree_Handler(sys.argv[1])
		x.set_max_values(tcp,obj)
		x.get_tree()
		x.post_process()
		#END TIME
		time_taken = time.time() - start
		#WRITE INTO FILE
		f.write( str(tcp) + "\t" + str(obj) + "\t" + str(time_taken))
f.close()