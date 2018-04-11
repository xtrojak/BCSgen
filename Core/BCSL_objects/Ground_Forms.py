import itertools
import copy
from functools import reduce

from .Reaction import *
from .Atomic import *
from .Structure import *
from .Complex import *

def atomicGroundForm(agent, allowedStates):
	if agent.state == "_":
		return set([AtomicAgent(agent.name, state) for state in allowedStates])
	return set([agent])

def structureGroundForm(agent, allowedAtomics, atomicSignatures):
	names = allowedAtomics - agent.getAtomicNames()
	atomics = []
	for name in names:
		atomics.append(atomicGroundForm(AtomicAgent(name, "_"), atomicSignatures[name]))
	if agent.composition:
		atomics = [agent.composition] + atomics

	if len(atomics) == 1 and len(agent.composition) == len(atomics[0]):
		cartesian = [tuple(agent.composition)]
	else:
		cartesian = itertools.product(*atomics)
	results = [StructureAgent(agent.name, set(composition)) for composition in cartesian]
	return set(results)

def pairStructuresGroundForm(agent1, agent2, atomicSignatures, structureSignatures):
	if agent1.name in structureSignatures and agent2.name in structureSignatures:
		groundedAgents1 = structureGroundForm(agent1, structureSignatures[agent1.name], atomicSignatures)
		groundedAgents2 = structureGroundForm(agent2, structureSignatures[agent2.name], atomicSignatures)
		pairs = itertools.product(groundedAgents1, groundedAgents2)
		return set([agents_grounded for agents_grounded in pairs if containsSameNames(agent1, agents_grounded[0], agent2, agents_grounded[1])])
	return set()

def pairAtomicsGroundForm(agent1, agent2, atomicSignatures):
	grounded1 = atomicGroundForm(agent1, atomicSignatures[agent1.name])
	grounded2 = atomicGroundForm(agent2, atomicSignatures[agent2.name])
	return set(zip(grounded1, grounded2))  # maybe copy is needed

def containsSameNames(agent1_origin, agent1_grounded, agent2_origin, agent2_grounded):
	return agent1_grounded.exceptTheseNames(agent1_origin.getAtomicNames()) == \
		agent2_grounded.exceptTheseNames(agent2_origin.getAtomicNames())

def indicesGroundForm(omega, Indices, atomicSignatures, structureSignatures):
	results = []
	for (i, j) in Indices:
		if i is None:
			if type(omega[j]) is AtomicAgent:
				gf = atomicGroundForm(omega[j], atomicSignatures[omega[j].name])
				nones = [None] * len(gf)
				results.append(set(zip(nones, gf))) # (None, AA)
			else:
				gf = structureGroundForm(omega[j], structureSignatures[omega[j].name], atomicSignatures)
				nones = [None] * len(gf)
				results.append(set(zip(nones, gf))) # (None, SA)
		elif type(omega[i]) is AtomicAgent:
			if j is None:
				gf = atomicGroundForm(omega[i], atomicSignatures[omega[i].name])
				nones = [None] * len(gf)
				results.append(set(zip(gf, nones))) # (AA, None)
			else:
				results.append(pairAtomicsGroundForm(omega[i], omega[j], atomicSignatures)) # (AA, AA)
		else:
			if j is None:
				gf = structureGroundForm(omega[i], structureSignatures[omega[i].name], atomicSignatures)
				nones = [None] * len(gf)
				results.append(set(zip(gf, nones))) # (SA, None)
			else:
				results.append(pairStructuresGroundForm(omega[i], omega[j], atomicSignatures, structureSignatures)) # (SA, SA)
	return results

def ruleGroundForm(rule, atomicSignatures, structureSignatures):
	results = indicesGroundForm(rule.omega, rule.Indices, atomicSignatures, structureSignatures)
	combinations = list(itertools.product(*results))
	return [zip(*combo) for combo in combinations]

def createReactions(rules, atomicSignatures, structureSignatures, inputRates):
	if len(rules) != len(inputRates):
		inputRates = [1] * len(rules)
	reactions = []
	rates = []
	for rule, rate in zip(rules, inputRates):
		tmpRxns = ruleGroundForm(rule, atomicSignatures, structureSignatures)
		for rxn in tmpRxns:
			sequence = list(itertools.chain.from_iterable(rxn))
			sequence = [x for x in sequence if x]
			seq = [Complex(sequence[rule.indexMap[i] + 1:rule.indexMap[i + 1] + 1], rule.chi[i].compartment) for i in range(len(rule.indexMap) - 1)]
			reaction = Reaction(seq, rule.I)
			if reaction not in reactions:
				reactions.append(reaction)
				rates.append(rate)
	return reactions, rates
