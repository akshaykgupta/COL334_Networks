import os,Q4,sys,time
import platform as pf

if(len(sys.argv) != 2):
	print 'Syntax for correct usage: python timing.py <HAR file/OBJ Tree source>'
	exit()

#Edit these:
max_tcp = 8
max_obj = 8 
f = open("timing_analysis.data" , "w")
f.write('Max TCP \t Max OBJ \t Time Taken')
for tcp in range(1,max_tcp):
	for obj in range(1,max_obj):
		# Flushing the DNS cache
		operating_system = pf.system()
		if (operating_system == "Linux"):
			os.system("rndc restart")
		elif operating_system == "Windows":
			os.system("ipconfig /flushdns")
		elif operating_system == "Darwin":
			os.system("dscacheutil -flushcache")
		else:
			print 'Unrecognized OS. Quitting...'
			exit()
		
		#.idx for mapping index files.
		index_file = "mapping_for_" + str(tcp) + "_" + str(obj) + ".idx"
		directory_name = "dl_" + str(tcp) + "_" + str(obj)
		
		if(not os.path.exists(directory_name)):
			os.makedirs(directory_name)
		
		the_downloader = Q4.downloader()
		
		the_downloader.set_constants(index_file,directory_name)
		#....Starting......
		start = time.time()
		x = the_downloader.object_Tree_Handler(sys.argv[1])
		x.set_max_values(tcp,obj)
		x.get_tree()
		x.post_process()
		#....Ending......
		time_taken = time.time() - start

		#Writing to file
		f.write( str(tcp) + "\t" + str(obj) + "\t" + str(time_taken))
f.close()