from pprint import pprint
import numpy as np
import sys
import os

# todo: add some cmdline options

input_fpath = "results/test.json"
output_fpath = input_fpath.replace(".json", "_processed.json")


"""
TO BE DEFINED!!!
Output schema:
{
	"gateways": {
		0:			#integer gateway id
			"pos":
				"X":	#gateway x coord
				"Y":	#gateway y coord
				"Z":	#gateway z coord
		1: ...
	}
	
	"devices": {
		0:						#integer device id
			"initialPos":
				"X":			#initial device x coord
				"Y":			#initial device x coord
				"Z":			#initial device x coord
			"pos":
				"X": [ ... ]	#vector of x coordinates recorded when a message is sent
				"Y": [ ... ]	#vector of y coordinates recorded when a message is sent
				"Z": [ ... ]	#vector of z coordinates recorded when a message is sent
		1: ...
	}

	"messages": [  		#ordered list of sent messages
		{
			"devId":			#integer device id that sent the message
			"msgId":			#integer message id of the device. This id is coherent with the position of the message in the list ["devices"]["pos"]["X"/"Y"/"Z"]
			"recipients": {		#contains the ids of the gateways that have received the message
				42: {			#integer id of a gateway receiving the message
					"time":		#simulation time when it was received
					"rssi":		#double, rssi value
				}
				1337: ...
			}
		}
	]
}
"""
output = {}

print(f"[*] Loading results from: {input_fpath}")
results = eval(open(input_fpath).read())
print("[+] Results loaded")


# There should be only one root key in the JSON
if len(results.keys()) > 1:
	print("[!] WARNING: more than one JSON root key")
root_key = list(results.keys())[0] 
vectors = results[root_key]["vectors"]
scalars = results[root_key]["scalars"]
