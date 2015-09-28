import socket, sys, json




''' 
The code below essentially reads all objects, and requests all objects which 
'''

objects = []
id_lvl = {} # Maps id to level.
def all_requests(fpath):
	global objects,id_lvl
	f = open(fpath)
	for line in f:
		things = line.split(",") #Split by commas - current-id, url, parent-id is the format.
		object = {} # Presently empty. Must populate.
		object["cid"] = eval(things[0])
		object["pid"] = eval(things[2]) #What is this black magic eval?
		object["url"] = things[1]
		object["domain"] = things[1].split("/")[2] # http: / / www... / extra-stuff 
		#Need to establish lvl.
		if str(eval(things[2])) not in id_lvl:
			id_lvl[str(eval(things[2]))] = -1 #We add +1 to this later.
		id_lvl[str(eval(things[0]))] = id_lvl[str(eval(things[2]))] + 1
		objects.append(object)
	f.close()

def request(reqs , lvl):
	global objects, id_lvl
	#Need to request all the things at lvl in req.
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM , 0)
	cur_dom = objects[0]["domain"]
	print(cur_dom)
	sock.connect((objects[0]["domain"],80))
	f = open("brute-mapping.dmp", "w")
	for id in range(0,len(objects)):
		object = objects[id]
		if ( id_lvl[str(object["cid"])] == lvl ):
			#Now to request for the object.
			if ( cur_dom == object["domain"] ):
				#Do Nothing
				pass
			else:
				sock.close()
				sock.connect((object["domain"], 80))
				cur_dom = object["domain"]
			str_req = "GET " + object["url"] + " HTTP/1.1\r\nHost: " + object["domain"] + "\r\nConnection: keep-alive\r\n\r\n"
			sock.send(str_req)
			f.write(str(id) + str_req + "\n")
			newf = open("brute_dumps/" + str(id)+".response" , "w")
			
			did_i_write_flag = False
			while(True):
				try:
					data = sock.recv(1024)
				except:
					print(" Error occurred! sock.recv ka try catch failed. Request is as follows:\n")
					print(str_req)
					print("\n\n")
					print ( "received data = " + data)
					data = ""
				if ( len(data) == 0 ):
					break
				else:
					newf.write(data)
					did_i_write_flag = True
			newf.close()
			if ( not did_i_write_flag ):
				#This request ke liye nothing was written.
				print("### NOTHING WAS WRITTEN FOR: ###\n")
				print(str(id) + str_req + "\n")
	f.close()

all_requests("../dumps/www.vox.com.objt") #Get all the requests into a list of dictionaries.
lvl_requested = 1
print id_lvl
request(objects, lvl_requested)