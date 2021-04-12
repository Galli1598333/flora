from pprint import pprint
from tqdm import tqdm
import numpy as np
import sys
import os
import re

# todo: add some cmdline options

input_fpath = "simulations/results/test.json"
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

# Fetch number of gateways
# if this yields error make sure that numberofgateways is the first parameter in .ini file 
nGws = int(results[root_key]["moduleparams"][0]["**.numberOfGateways"])
nDevs = int(results[root_key]["moduleparams"][1]["**.numberOfNodes"])
# Calculate total number of sent messages
nTotMsgs = 0
for elem in scalars:
	if elem["name"] == "sentPackets" and re.match(r"LoRaNetworkTest.loRaNodes\[\d+\].SimpleLoRaApp", elem["module"]):
		nTotMsgs += elem["value"]
print(f"[+] {nTotMsgs} packets, {nDevs} devices, {nGws} gateways")

# Accumulate messages. Each entry is (time, device id, message id)
totMessagesTmp = []
for elem in tqdm(vectors, desc="Accumulate packets"):
	if elem["name"] == "counter Vector" and re.match(r"LoRaNetworkTest.loRaNodes\[\d+\].SimpleLoRaApp", elem["module"]):
		devId = int(elem["module"].split("[")[1].split("]")[0])   #take the device id enclosed in "[]"
		toAddMsgId = list(elem["value"])
		toAddTime = list(elem["time"])
		totMessagesTmp += [(t, devId, int(msgId)) for t, msgId in zip(toAddTime, toAddMsgId)]
		# TODO add to totMessagesTmp also X Y Z
# Sort by time
totMessagesTmp.sort(key=lambda x: x[0])

# Construct a mapping (device id, message id) --> message UID
messages2id = {(msg[1], msg[2]): i for i, msg in enumerate(totMessagesTmp)}
# Construct a mapping message UID --> (time sent, device id, message id)
id2messages = {i: msg for i, msg in enumerate(totMessagesTmp)}

# Alloc result message tensor
messages = np.zeros((nTotMsgs, nGws, 2))
# Initialize result devices dict
devices = {i: { 
		"nDevMsgs": 0,
		"msgIds": [],
		"msgPos": {"X": [], "Y":[], "Z":[]},
		"msgTimes": [],
	} for i in range(nDevs)
}

for gw in tqdm(range(nGws), desc="Extract received messages"):
	for elem in vectors:
		# Populate aux lists containing one entry per packet received by the gateway
		if elem["name"] == "Gateway / Received Message Id" and elem["module"] == f"LoRaNetworkTest.loRaGW[{gw}].packetForwarder":
			gw_times = list(elem["time"])
			gw_msgid = list(elem["value"])
		if elem["name"] == "Gateway / Received Device Id" and elem["module"] == f"LoRaNetworkTest.loRaGW[{gw}].packetForwarder":
			gw_devid = list(elem["value"])
		if elem["name"] == "Gateway / Received RSSI" and elem["module"] == f"LoRaNetworkTest.loRaGW[{gw}].packetForwarder":
			gw_rssi = list(elem["value"])
	gw_messages = [(t, devId, msgId, rssi) for t, devId, msgId, rssi in zip(gw_times, gw_devid, gw_msgid, gw_rssi)]
	print(f"[+] Gateway {gw} received {len(gw_messages)} messages")
	
	for msg in gw_messages:
		# Populate messages tensor
		t_recv, devId, msgId, rssi = msg
		msgUID = messages2id[(devId, msgId)]
		messages[msgUID, gw, 0] = t_recv
		messages[msgUID, gw, 1] = rssi
		# Populate device message id
		t_sent, devId_, msgId_ = id2messages[msgUID]
		assert(devId == devId_)
		assert(msgId == msgId_)
		devices[devId]["msgIds"].append(msgUID)
		devices[devId]["msgTimes"].append(t_sent)
		

# TODO finally sort messages in "devices" dict by time
# TODO write nDevMsgs in devices[x]		




