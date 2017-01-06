from time import time
import sys
import os.path
sys.path.append(os.path.abspath('../Core/'))
import State_space_generator as Gen
import Implicit_reaction_network_generator as Implicit

from Tkinter import *
from tkFileDialog import askopenfilename, asksaveasfilename
import tkFont
from tkMessageBox import *

"""
Application is main framework for the GUI
"""
class Application(Frame):

    def generate(self, myNet, state):
        myNet = Implicit.generateReactions(myNet)
        myNet.printReactions(self.reactions)
        self.len_reactions.config(text="Reactions: " + str(myNet.getNumOfReactions()))
        bound = myNet.calculateBound()
        states, edges, orderedAgents = Gen.generateStateSpace(myNet, state, bound)
        self.len_states.config(text="States: " + str(len(states)))
        self.len_edges.config(text="Edges: " + str(len(edges)))
        Gen.printStateSpace(states, edges, orderedAgents, self.stateSpace)

    """
    Checks if all fields are filled
    """
    def get_ready(self, *args):
        if self.model and self.stateSpace and self.reactions:
           self.compute.config(state=NORMAL)

    """
    Computes the state space above set parameters
    """
    def compute(self):
        myNet, state, networkStatus, message = Implicit.initializeNetwork(self.model)
        if networkStatus:
            self.generate(myNet, state)
        else:
            if askyesno("Conflicts", message):
                self.generate(myNet, state)
            else:
                f = open(os.path.basename(self.model) + ".log",'w')
                f.write(message[:-40])
                f.close()
                self.len_reactions.config(text="Reactions: N/A")
                self.len_states.config(text="States: N/A")
                self.len_edges.config(text="Edges: N/A")
        
        self.compute.config(text="Finish")
        self.compute.config(command=root.destroy)

    """
    Sets path to file with rules
    """
    def set_model(self):
        self.model = askopenfilename(filetypes = [('BCSL model', ('.bcs'))])
        self.text_model.config(state=NORMAL)
        self.text_model.delete(0, END)
        self.text_model.insert(END, self.model.__str__())
        self.text_model.config(state="readonly")

    """
    Sets path to output stateSpace file 
    """
    def set_stateSpace(self):
        self.stateSpace = asksaveasfilename(title = "State space file", filetypes = [('JSON', ('.json'))])
        self.text_stateSpace.config(state=NORMAL)
        self.text_stateSpace.delete(0, END)
        self.text_stateSpace.insert(END, self.stateSpace.__str__())
        self.text_stateSpace.config(state="readonly")

    def set_reactions(self):
        self.reactions = asksaveasfilename(title = "Reactions file", filetypes = [('Text file', ('.txt'))])
        self.text_reaction.config(state=NORMAL)
        self.text_reaction.delete(0, END)
        self.text_reaction.insert(END, self.reactions.__str__())
        self.text_reaction.config(state="readonly")


    """
    This is where visual behaviour is maintained
    """
    def createWidgets(self):
        self.mes = Label(root,text='Input', width=13, font="bold", borderwidth=8, relief= RIDGE)
        self.mes.grid(row=0, column=0, columnspan=2, ipadx=105)

        self.text_model = Entry(root,width=20, state="readonly", selectbackground='gray', readonlybackground='white', textvariable=self.modelVar)
        self.text_model.grid(row=1, column=1)

        self.button_rules = Button(root,text="Model",command=self.set_model, width=15)
        self.button_rules.grid(row=1, column=0)

        self.mes = Label(root,text='Output', width=14, font="bold", borderwidth=8, relief= RIDGE)
        self.mes.grid(row=3, column=0, columnspan=2, ipadx=100)

        self.text_stateSpace = Entry(root,width=20, state="readonly", selectbackground='gray', readonlybackground='white', textvariable=self.stateSpaceVar)
        self.text_stateSpace.grid(row=4, column=1)

        self.button_stateSpace = Button(root,text="State space file",command=self.set_stateSpace, width=15)
        self.button_stateSpace.grid(row=4, column=0)

        self.text_reaction = Entry(root,width=20, state="readonly", selectbackground='gray', readonlybackground='white', textvariable=self.reactVar)
        self.text_reaction.grid(row=6, column=1)

        self.button_reaction = Button(root,text="Reactions file",command=self.set_reactions, width=15)
        self.button_reaction.grid(row=6, column=0)

        self.mes = Label(root,text='Results', width=15, font="bold", borderwidth=8, relief= RIDGE)
        self.mes.grid(row=7, column=0, columnspan=2, ipadx=95)

        self.state_space = Label(root,text="State space", width=20, font=tkFont.Font(family="TkDefaultFont",size=9, underline=1))
        self.state_space.grid(row=8, column=0)

        self.reaction_network = Label(root,text="Reaction network", width=20, font=tkFont.Font(family="TkDefaultFont",size=9, underline=1))
        self.reaction_network.grid(row=8, column=1)

        self.len_states = Label(root,text="States:",  width=20)
        self.len_states.grid(row=9, column=0)

        self.len_reactions = Label(root,text="Reactions:",  width=20)
        self.len_reactions.grid(row=9, column=1)

        self.len_edges = Label(root,text="Edges:",  width=20)
        self.len_edges.grid(row=10, column=0)

        self.compute = Button(root,text="Compute",command=self.compute, width=15, state=DISABLED)
        self.compute.grid(row=12, column=1)

        self.exit = Button(root,text="Cancel",command=root.destroy, width=15)
        self.exit.grid(row=12, column=0)

        self.stateSpaceVar.trace("w", self.get_ready)
        self.modelVar.trace("w", self.get_ready)
        self.reactVar.trace("w", self.get_ready)

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.reactions = None
        self.stateSpace = None
        self.model = None
        self.stateSpaceVar = StringVar()
        self.reactVar = StringVar()
        self.modelVar = StringVar()
        self.numOfReactions = StringVar()
        self.grid()
        self.createWidgets()

root = Tk()
root.option_add("*Dialog.msg.wrapLength", "20i")
root.title("BCSgen state space generating")
app = Application(master=root)
app.mainloop()