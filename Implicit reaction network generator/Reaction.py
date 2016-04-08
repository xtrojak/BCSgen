import sys
import os
sys.path.append(os.path.abspath('../Explicit state space generator'))
from State import *

def create_string_chain(side):
    new_side = map(lambda (a, n): n.__str__() + " " + a.__str__(), side.getAgents().items())
    return " + ".join(new_side)

class Reaction:
    def __init__(self, left_hand_side, right_hand_side):
        self.left_hand_side = left_hand_side
        self.right_hand_side = right_hand_side

    def __eq__(self, other):
        return self.left_hand_side == other.left_hand_side and self.right_hand_side == other.right_hand_side

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return create_string_chain(self.left_hand_side) + " -> " + create_string_chain(self.right_hand_side)

    def __hash__(self):
        return hash((str(self.left_hand_side), str(self.right_hand_side)))

    def __lt__(self, other):
        return self.__repr__() < other.__repr__()

    def getLeftHandSide(self):
        return self.left_hand_side

    def getRightHandSide(self):
        return self.right_hand_side