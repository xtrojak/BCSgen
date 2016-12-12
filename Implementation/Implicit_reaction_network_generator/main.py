import sys
from Network import *

inputFile = sys.argv[-2]
outputFile = sys.argv[-1]

# initialize the network and create it
myNet = Network()
myNet.createNetwork(inputFile)

networkStatus, message = myNet.applyStaticAnalysis()  # apply static analysis

if not networkStatus:
	print message
else: 	# if network is OK, proceed

	old_numberOfReactions = 0
	new_numberOfReactions = -1

	while old_numberOfReactions != new_numberOfReactions: 	# while there are some new reactions
		globallyNewAgents = myNet.interpretEdges()			# interpret rules with new agents
		myNet.introduceNewAgents(globallyNewAgents)			# put new agents to buckets

		old_numberOfReactions = new_numberOfReactions
		new_numberOfReactions = myNet.getNumOfReactions()

	myNet.printReactions(outputFile)