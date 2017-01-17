import copy
import collections
import itertools
from Structure_Agent import *

"""
Checks if for every agent from full composition_s there exist unique compatible agent from full composition_l (order is NOT important)
:param composition_s:  solution's full composition (List)
:param composition_l: left-hand-side's full composition (List)
:return: True if the condition is satisfied
"""
def softCompareFullCompositions(composition_s, composition_l):
    if not composition_l:
        return True
    for agent in composition_s:
        if agent.isSimilarTo(composition_l[0]):
            return softCompareFullCompositions(extractValue(composition_s, agent), composition_l[1:])
    return False

"""
Checks if for every agent from full composition_s there exist unique compatible agent from full composition_l
:param composition_s:  candidate's full composition (List)
:param composition_l: left-hand-side's full composition (List)
:return: True if the condition is satisfied
"""
def compareFullCompositions(composition_s, composition_l):
    for i in range(len(composition_s)):
        if not composition_s[i].isCompatibleWith(composition_l[i]):
            return False
    return True

class Complex_Agent:
    def __init__(self, full_composition, compartment):
        self.full_composition = list(full_composition)
        self.compartment = compartment

    def __eq__(self, other):
        if isinstance(other, Complex_Agent):
            return collections.Counter(self.full_composition) == collections.Counter(other.full_composition) and self.compartment == other.compartment
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ".".join(map(lambda k: k.__repr__(), self.full_composition)) + "::" + self.compartment

    def __hash__(self):
        return hash((str(self.full_composition), self.compartment))

    def __lt__(self, other):
        return self.__repr__() < other.__repr__()

    def getFullComposition(self):
        return self.full_composition

    def getCompartment(self):
        return self.compartment

    def setFullComposition(self, full_composition):
        self.full_composition = full_composition

    def setCompartment(self, compartment):
        self.compartment = compartment

    def getAllCompositions(self):
        return [Complex_Agent(element, self.compartment) for element in itertools.permutations(self.full_composition, len(self.full_composition))]

    """
    Checks if the first complex agent is compatible with the second one
    :param other: the second agent
    :return: True if it is compatible
    """
    def isCompatibleWith(self, other):
        if not isinstance(other, Complex_Agent):
            return False
        return ( self.compartment == other.compartment and len(self.full_composition) == len(other.full_composition)
                and compareFullCompositions(copy.deepcopy(self.full_composition), copy.deepcopy(other.full_composition)) )

    """
    Checks if the first complex agent is similar to the second one
    :param other: the second agent
    :return: True if it is similar
    """
    def isSimilarTo(self, other):
        if not isinstance(other, Complex_Agent):
            return False
        return ( self.compartment == other.compartment and len(self.full_composition) == len(other.full_composition) and softCompareFullCompositions(copy.deepcopy(self.full_composition), copy.deepcopy(other.full_composition)) )

    """
    Returns compatible agent (first found) from full composition with given agent
    :param agent: given atomic or structure agent
    :return: compatible agent
    """
    def getCompatibleAgent(self, agent):
        for full_agent in self.full_composition:
            if agent.isCompatibleWith(full_agent):
                return full_agent
        return None

    """
    Returns all indices of the compatible agents from full composition with given agent
    :param agent: given atomic or structure agent
    :return: list indices of compatible agents
    """
    def getAllCompatibleAgents(self, agent):
        return [i for i, full_agent in enumerate(self.full_composition) if agent.isCompatibleWith(full_agent)]

    def maxOccurence(self):
        names = collections.Counter(map(lambda agent: agent.getName(), self.full_composition))
        return max(names.values())

    """
    Changes state of Complex agent accoring to given other complex agent
    :param other: given other complex agent
    :return: new Complex agent with changed states
    """
    def changeState(self, other):
        rhs_composition = copy.deepcopy(self.full_composition)
        candidate_composition = other.full_composition
        candidate_composition = map(lambda i: rhs_composition[i].changeState(candidate_composition[i]), range(len(rhs_composition)))
        return Complex_Agent(sorted(candidate_composition), self.compartment)
