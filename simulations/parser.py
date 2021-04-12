from pprint import pprint
import numpy as np
import sys
import os

# todo: add some cmdline options

input_fpath = "results/test.json"
output_fpath = input_fpath.replace(".json", "_processed.json")


"""
- - - WORK IN PROGRESS - - -

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

	"nTotMsgs":	1337				#integer, total number of sent messages
	"messages": [					#3-dimensional tensor, expressed as list of lists of lists. Has shape (nTotMsgs, nGws, 2), where nGws is the number of gateways
		[
			(time_gw0, rssi_gw0),
			(time_gw1, rssi_gw1),
			(time_gw2, rssi_gw2),
			...
		],
		[ 
			...
		],
		...
	]

	# messages is a tensor:
	#
	#		--	  	gw1				gw2				gw3				...		gwM
	#	________________________________________________________________________
	#	|	msg1  |	(time, rssi)	(time, rssi)	(time, rssi)
	#	|	msg2  |	(time, rssi)	(....)
	#	|	msg3  |	...
	#	|	msg4  |
	#	|	...	  |
	#	|	msgN  |
	#
	#
	#	So for example messages[42][2][0] will retrieve the time in which the gateway with id 2 
	#	has received the message with id 42. Similarly messages[42][2][1] retrieves the rssi
	#

	
	"devices": {
		0: {						#integer device id
			"nDevMsgs": 42			#integer, number of sent messages by the device. The sum of "nDevMsgs" for all devices is equal to "nTotMsgs"
			"msgIds": [				#list of message id sent by the device. The indices in this list are the indices in "messages" tensor corresponding to packets sent by the device. Has length "nDevMsgs"
				3,					#assuming numpy is used, to isolate the packets sent by a device it should suffice to do messages[msgIds]
				5,
				6,
				10,
				...
			]
			"msgPos": {
				"X": [ ... ]		#vector of x coordinates recorded when a message is sent. i-th entry references the i-th sent packet of the device. Has length "nDevMsgs" 
				"Y": [ ... ]		#vector of y coordinates recorded when a message is sent. i-th entry references the i-th sent packet of the device. Has length "nDevMsgs" 
				"Z": [ ... ]		#vector of z coordinates recorded when a message is sent. i-th entry references the i-th sent packet of the device. Has length "nDevMsgs" 
			}
			"msgTimes": [ ... ] 	#list of times in which a message was sent by the device, one timestamp per message. Has length "nDevMsgs"
		},

		1: { ... }
	}
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
