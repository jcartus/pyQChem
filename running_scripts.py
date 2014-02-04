# pyQchem - Input/Output-Tools for Q-Chem
# Copyright (C) 2014  Matthew Goldey

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#####################################################################
#                                                                   #
#                 pyQchem - Scripts for running Q-Chem              #
#                                                                   #
#####################################################################

from input_classes import *

def qcrun(inp_file,name='',loc53='',qchem='',nt=1,np=1,timestamp=False):
    """This is a script for running Q-Chem inside of iPython given an input file object, name, 53.0 file, location, and number of threads or processors"""
    #tag it all with current time for safety's sake
    import time,os
    curtime=time.strftime("%Y%m%d%H%M%S")
    if name=='':
        name=inp_file.name
    if name=='':
        name=curtime
    if timestamp!=True:
        name=name.replace(".in","")
    else: 
        if name.endswith(".in"):
            name.replace(".in",curtime)
        else:
        	name=name+curtime


    #make script file
    scr=name+".sh"
    scr_out=open(scr,'w')

    #source appropriate Q-Chem
    if qchem!='':
        scr_out.write("source ~/"+qchem+"\n")

    #copy 53.0 if restarting
    if loc53!='':
        inp_file.rem.scf_guess('read')
        scr_out.write("mkdir $QCSCRATCH/"+name+".dir\n")
        if loc53.endswith(".in.53.0"):
            scr_out.write('cp '+loc53+' $QCSCRATCH/'+name+'.dir/53.0\n')
        else:
            scr_out.write('cp '+loc53+'/53.0 $QCSCRATCH/'+name+'.dir/\n')

    inp_file.write(name+".in")

    #write qchem command to script file
    if nt>1:
    	scr_out.write("qchem -nt "+str(nt)+" "+name+".in "+name+".out "+name+".dir "+"\n")
    elif np>1:
    	scr_out.write("qchem -np "+str(nt)+" "+name+".in "+name+".out "+name+".dir "+"\n")
    else:
    	scr_out.write("qchem "+name+".in "+name+".out "+name+".dir "+"\n")

    #close and run
    scr_out.close()
    os.popen("bash "+scr).read()
    return

def queue(joblist,num_workers=1):
	"""This is a simple queue for running through a list of jobs.
	When in doubt, set num_workers to the number of cores on the machine.
	Advanced options are currently not supported."""
	import Queue
	import threading
	q_in = Queue.Queue(maxsize=0)
	q_out = Queue.Queue(maxsize=0)
	# process that each worker thread will execute until the Queue is empty
	def worker():
	    while True:
	        # get item from queue, do work on it, let queue know processing is done for one item
	        item = q_in.get()
	        qcrun(item)
	        q_out.put(item.name)
	        q_in.task_done()

	# another queued thread we will use to print output
	def printer():
	    while True:
	        # get an item processed by worker threads and print the result. Let queue know item has been processed
	        item = q_out.get()
	        print "Completed ", item
	        q_out.task_done()

	# launch all of our queued processes
	# Launches a number of worker threads to perform operations using the queue of inputs
	for i in range(num_workers):
	     t = threading.Thread(target=worker)
	     t.daemon = True
	     t.start()

	# launches a single "printer" thread to output the result (makes things neater)
	t = threading.Thread(target=printer)
	t.daemon = True
	t.start()

	# put items on the input queue
	for item in joblist:
		q_in.put(item)

	# wait for two queues to be emptied (and workers to close)
	q_in.join()       # block until all tasks are done
	q_out.join()

	print "Processing Complete"