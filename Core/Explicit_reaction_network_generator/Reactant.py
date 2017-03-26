from Agent import *

def removeDuplicites(seq):
	seen = set()
	seen_add = seen.add
	return [x for x in seq if not (x in seen or seen_add(x))]

class Reactant:
	def __init__(self, item):
		self.name = item
		part = item.split("::")
		self.compartment = part[1]
		self.agents = sorted(removeDuplicites(map(Agent, part[0].split('.'))))

	def __eq__(self, other):
		return self.name == other.name

	def __hash__(self):
		return hash(self.name)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return ".".join(map(str, self.agents)) + "::" + self.compartment

	def __lt__(self, other):
		return str(self) < str(other)