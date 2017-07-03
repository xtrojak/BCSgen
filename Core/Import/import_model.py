import sys
import copy
import re
import os
import json
import numpy as np
import subprocess
import threading

sys.path.append(os.path.abspath('../'))
import Explicit_reaction_network_generator as Explicit
import State_space_generator as Gen

parserPath = sys.argv[-1]
sys.path.append(os.path.abspath(parserPath))
from RuleParser import *

#####################################################################

class Rule():
	def __init__(self, index, text, length):
		self.index = index
		self.text = text.split("@")[0]
		self.length = length

"""
If first given string is a number, return (number - 1) multiplied second string joined by sign "+"
:param s1: first string
:param 21: second string
:return: first string if condition is not satisfied
"""
def multiply_string(s1, s2):
	if s1.isdigit():
		return "+".join([s2] * (int(s1) -1) + [""])
	else:
		return s1

"""
Cleans rule (string) from steichiometry by multiplying appropriate agent
:param rule: given rule in string form
:return: rule without steichiometry
"""
def remove_steichiometry(rule):
	new_rule = []
	splitted_rule = rule.split(" ")
	for i in range(len(splitted_rule) - 1):
		new_rule.append(multiply_string(splitted_rule[i], splitted_rule[i + 1]))
	new_rule.append(splitted_rule[len(splitted_rule) - 1])
	return "".join(new_rule)

"""
Removes duplicated white spaces from a string
:param rule: given string
:return: clean string
"""
def remove_spaces(rule):
	splitted_rule = rule.split(" ")
	splitted_rule = filter(None, splitted_rule)
	return " ".join(splitted_rule)

"""
Imports agent names for initial state
:param init_file: file containing lines number agent
:return: initial State
"""
def import_initial_state(inits):
	agents = []
	for line in inits:
		line = line.rstrip()
		for i in xrange(0, int(line.split(" ")[0])):
			agents.append(line.split(" ")[1])
	return agents

def import_rules(input_file):
	inits, created_rules, rates = [], [], []

	lines = filter(None, input_file.split("\n"))

	lineNum = 0
	for line in lines:
		line = str(line)
		lineNum += 1
		if line.startswith('#') and lineNum != 1:
			for line in lines[lineNum:]:
				inits.append(str(line))
			break
		elif not line.startswith('#') and not line.isspace():
			rule = line.split("@")
			if len(rule) > 1:
				rates.append(rule[1])
			rule = rule[0]
			rule = remove_spaces(rule)			# maybe not needed?
			rule = remove_steichiometry(rule)	# maybe not needed?
			created_rules.append(Rule(lineNum, rule, len(line)))
	return created_rules, import_initial_state(inits), rates

def getPositionOfRule(index, rules):
	return sum(map(lambda rule: rule.length + 1, rules[:index])) + 8

def createMessage(unexpected, expected):
	if unexpected:
		if len(expected) > 1:
			return "Syntax error: unexpected token '" + unexpected + "' where one of '" + ", ".join(expected) + "' is expected."
		elif len(expected) == 1:
			return "Syntax error: unexpected token '" + unexpected + "' where '" + expected[0] + "' is expected."
		else:
			return "Syntax error: unexpected token '" + unexpected + "'."
	else:
		return "Syntax error: unexpected end of line."

def verifyRules(rules):

	# here goes new parser version
	results = []
	for rule in rules:
		results.append(parseEquations(rule.text))

	for i in range(len(results)):
		# print results[i] # problem with parsing of :: (when its omited)

		result = json.loads(results[i])
		if "error" in result:
			start = int(result["start"]) + getPositionOfRule(i, rules)
			if result["unexpected"] == "end of input":
				unexpected = None
				end = start
			else:
				unexpected = result["unexpected"]
				end = start + len(result["unexpected"])
			message = createMessage(unexpected, result["expected"])
			return [start, end, message], False

	return [], True

def computeReactions(rules, rates):
	reactionGenerator = Explicit.Compute()
	reactions, rates = reactionGenerator.computeReactions(map(lambda rule: rule.text, rules), rates)
	return reactions, rates

########################################################################

"""
Replaces all occurrences from defined substitutions for an agent
:param substitutions: substitution list of pair (from, to)
:param agents: list of agents (in sense of full composition)
:return: list of replaced + not replaced agents
"""
def replace_agents(substitutions, agents):
	new_agents = []
	copy_agents = copy.deepcopy(agents)
	for substate in substitutions:
		for agent in agents:
			if substate[0] == agent:
				new_agents += substate[1].split(".")
				copy_agents.remove(agent)
				break
	new_agents += copy_agents
	return new_agents

"""
Applies substitutions on each agent in a rule
:param substitutions: substitution list of pair (from, to)
:param rule_agent: given string
:return: list of replaced + not replaced agents
"""
def substitute(substitutions, rule_agent):
	splitted_rule_agent, semicolons = split_rule_agent(rule_agent)
	new_rule_agent = []
	while splitted_rule_agent != new_rule_agent:
		new_rule_agent = splitted_rule_agent
		splitted_rule_agent = map(lambda agents: replace_agents(substitutions, agents), splitted_rule_agent)
	new_rule_agent = map(lambda l: ".".join(l), new_rule_agent)
	return "".join(map(lambda (a, b): "".join([a, b]), zip(new_rule_agent[:-1], semicolons))) + new_rule_agent[-1]

"""
Splits rule to list of list by :: operators
 :!: means exists right one (E!)        ( n )
	same as ::                          ( 1 )

 :?: means exists number of them (E)    ( n ) + ( n ) + ... + ( n )
										( 1 )   ( 2 )         ( n )

 :*: means all of them                    1

:param rule_agent: given string
:return: list of agents, list of semicolons
"""
def split_rule_agent(rule):
	agents = rule.replace(":!:", "::").replace(":?:", "::").split("::")
	agents = map(lambda agent: agent.split("."), agents)
	semicolons = re.findall(r":.:|::", rule)
	return agents, semicolons

"""
Substitutes agents in a rule
:param substitutions: list of pairs (from_sub, to_sub)
:param rule: string representing rule
:return: string rule with substituted agents
"""
def substitute_rule(substitutions, rule):
	sides = rule.split("=>")
	rule_sides = []
	for side in sides:
		if side:
			agents = side.split("+")
			substitued_agents = map(lambda agent: substitute(substitutions, agent), agents)
			rule_sides.append("+".join(substitued_agents))
		else:
			rule_sides.append("")
	return "=>".join(rule_sides)

"""
This is flattening of agents of form a::T
then semicolon does not matter.
:param first_agent: an atomic agent
:param second_agent: a structure agent
:return: structure agent
"""
def flatten_aT(first_agent, second_agent):
	if first_agent in second_agent.getPartialComposition():
		return second_agent
	else:
		agent = second_agent.getCompatibleAtomicAgent(first_agent)
		second_agent.setPartialComposition(second_agent.getPartialComposition() - {agent} | {first_agent})
		return second_agent

"""
This is flattening of agents of form a::X
:param first_agent: an atomic agent
:param second_agent: a complex agent
:param semicolon: given semicolon type
:return: list of agent(s)
"""
def flatten_aX(first_agent, second_agent, semicolon):
	if semicolon == ":?:" or semicolon == "::":
		agent = second_agent.getCompatibleAgent(first_agent)
		new_composition = second_agent.getFullComposition()
		new_composition[new_composition.index(agent)] = first_agent
		second_agent.setFullComposition(new_composition)
		return [second_agent]
	elif semicolon == ":!:":
		new_agents = []
		indices = second_agent.getAllCompatibleAgents(first_agent)
		for index in indices:
			new_composition = copy.deepcopy(second_agent.getFullComposition())
			new_composition[index] = first_agent
			new_agents.append(BCSL.Complex_Agent(new_composition, second_agent.getCompartment()))
		return new_agents
	else:
		indices = second_agent.getAllCompatibleAgents(first_agent)
		new_composition = second_agent.getFullComposition()
		for index in indices:
			new_composition[index] = first_agent
		second_agent.setFullComposition(new_composition)
		return [second_agent]


def flatten_TX(first_agent, second_agent, semicolon):
	return

def flatten_XX(first_agent, second_agent, semicolon):
	return

"""
Flattens two agents according to given semicolon
:param first_agent: first agent
:param semicolon: given semicolon (::, :!:, :?: or :*:)
:param rest: second agent
:return: flattened agent
"""
def flattenPair(first_agent, second_agent, compartment, semicolon):
	first_agent = create_agent(first_agent + "::" + compartment)
	second_agent = create_agent(second_agent + "::" + compartment)

	if isinstance(first_agent, BCSL.Atomic_Agent) and isinstance(second_agent, BCSL.Structure_Agent):
		return flatten_aT(first_agent, second_agent)

	if isinstance(first_agent, BCSL.Atomic_Agent) and isinstance(second_agent, BCSL.Complex_Agent):
		return flatten_aX(first_agent, second_agent, semicolon)

	if isinstance(first_agent, BCSL.Structure_Agent) and isinstance(second_agent, BCSL.Complex_Agent):
		return flatten_TX(first_agent, second_agent, semicolon)

	if isinstance(first_agent, BCSL.Complex_Agent) and isinstance(second_agent, BCSL.Complex_Agent):
		return flatten_XX(first_agent, second_agent, semicolon)

"""
Flattens agent recursively
:param first_part: string agent
:param semicolons: associated semicolons
:param rest: rest of agents
:return: flattened agent
"""
def flattenAgent(first_part, compartment, semicolons, rest):
	if not rest:
		return first_part
	else:
		first_part = flattenPair(first_part, rest[0], compartment, semicolons[0])
		return flattenAgent(first_part, compartment, semicolons[1:], rest[1:])

"""
Transforms expanded string rule to flattened string rule.
:param rule: rule in extended form (with ::)
:return: rule in flattened form (without ::)
"""
def flattenRule(rule):
	sides = rule.split("=>")
	rule_sides = []
	for side in sides:
		agents = []
		agents = side.split("+")
		for agent in agents:
			semicolons = re.findall(r":.:|::", agent)[:-1]
			agent = agent.replace(":!:", "::").replace(":?:", "::").split("::")
			compartment = agents[-1]
			agents = agents[:-1]
			agents.append(flattenAgent(agent[0], compartment, semicolons, agent[1:]))
		rule_sides.append(" + ".join(agents))
	return " => ".join(rule_sides)

########################################################################
"""
Import state space section
"""

def parseState(state):
	return tuple(map(int, state.split("|")))

def importStateSpace(file):
	states = set()
	edges = set()
	with open(file, 'r') as f:
		data = json.load(f)

	for state, agents in data['nodes'].iteritems():
		states.add(parseState(state))

	uniqueAgents = list(map(str, data['unique']))

	for edge_id, value in data['edges'].iteritems():
		edges.add(Gen.Vector_reaction(np.array(parseState(value['from'])), np.array(parseState(value['to']))))

	return states, edges, uniqueAgents