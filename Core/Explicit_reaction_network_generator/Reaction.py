from Reactant import *

class Reaction:
	def __init__(self, line):
		self.name = line
		self.left = len(line.split("=>")[0].split("+"))
		line = line.replace("=>", "+")
		self.reactants = map(Reactant, line.split("+"))

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Reaction - " + self.name + ": | " + ", ".join(map(str, self.reactants)) + " |"