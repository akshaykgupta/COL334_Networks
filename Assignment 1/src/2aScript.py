import os
import datetime
import sched
import time
#hi comment!
#myip : 10.208.20.141

def observe():
	tim = datetime.datetime.now().strftime("%d/%m/%y %I:%M:%S %p")
	os.system("echo -n" + tim + ", >> 2aResults.csv")
	os.system("nmap -n -sP 10.208.20.141/24 | egrep -o \"([0-9]+) hosts up\" | egrep -o \"([0-9]+)\" >> 2aResults.csv")


schedule = sched.scheduler(time.time, time.sleep)
i = 0
while (i < 24*7 ): # TODO : 7*24 should be changed to the the number of observations we want to take
	schedule.enter( i*3600 , 1 , observe, ()) # TODO : 3600 should be the interval - 3600 SECONDS, i think.
	i = i+1
schedule.run()