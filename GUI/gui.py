import time
import sys
import os.path
import numpy as np
from PyQt4 import QtGui, QtCore, QtWebKit
from PyQt4.QtGui import *
import signal

sys.path.append(os.path.abspath('../Core/'))

import State_space_generator as Gen
import Implicit_reaction_network_generator as Implicit
import Import as Import
from Libraries import *

# global methods for creating PyQt objects

def createProgressBar(it):
	progressBar = QtGui.QProgressBar(it)
	progressBar.setRange(0,1)
	return progressBar

def createTextBox(it, text, style, readonly):
	box = QLineEdit(it)
	if text:
		box.setText(text)
	if style:
		box.setStyleSheet(style)
	box.setReadOnly(readonly)
	return box

def createButton(it, text, to_connect, disabled):
	button = QtGui.QPushButton(text, it)
	button.clicked.connect(to_connect)
	button.setDisabled(disabled)
	return button

def createAction(it, title, shortcut, tip, connectWith, icon):
	if icon:
		action = QtGui.QAction(icon, title, it)
	else:
		action = QtGui.QAction(title, it)
	if shortcut:
		action.setShortcut(shortcut)
	action.setStatusTip(tip)
	action.triggered.connect(connectWith)
	return action

"""
Class MainWindow
- the main window which holds all the widgets (how the app looks like)
"""
class MainWindow(QtGui.QMainWindow):
	def __init__(self, screenWidth, screenHeight, parent=None):
		super(MainWindow, self).__init__(parent)

		self.rulesAreCorrect = False

		self.screenWidth = screenWidth
		self.screenHeight = screenHeight

		self.rowDeleted = QLineEdit("0")
		self.rowDeleted.textChanged.connect(self.checkScrollArea)

		#########################################

		self.statusBar()

		icon = QtGui.QIcon.fromTheme("document-save")

		self.save = createAction(self, "Save model", "Ctrl+S", 'Save model to a file.', self.save_model, icon)

		icon = QtGui.QIcon.fromTheme("application-exit")

		self.exit = createAction(self, "Quit", "Ctrl+Q", 'Quit the program.', self.close, icon)

		icon = QtGui.QIcon.fromTheme("document-open")

		self.importSpace = createAction(self, "Import state space", "Ctrl+J", 'Import state space from a JSON file.', self.importStateSpace, icon)
		self.loadModel = createAction(self, "Import model", "Ctrl+L", 'Import model from a file.', self.open_model, icon)

		mainMenu = self.menuBar()
		fileMenu = mainMenu.addMenu('File')

		fileMenu.addAction(self.save)
		fileMenu.addSeparator()
		fileMenu.addAction(self.loadModel)
		fileMenu.addAction(self.importSpace)
		fileMenu.addSeparator()
		fileMenu.addAction(self.exit)

		icon = QtGui.QIcon.fromTheme("edit-undo")

		self.undo = createAction(self, "Undo", "Ctrl+Z", 'Undo last action.', self.undoText, icon)

		icon = QtGui.QIcon.fromTheme("edit-redo")

		self.redo = createAction(self, "Redo", "Ctrl+Y", 'Redo last action.', self.redoText, icon)

		icon = QtGui.QIcon.fromTheme("edit-clear")

		self.clear = createAction(self, "Clear", "Ctrl+R", 'Clear all the text.', self.clearText, icon)

		icon = QtGui.QIcon.fromTheme("edit-copy")

		self.copy = createAction(self, "Copy", "Ctrl+C", 'Copy selected text to clipboard.', self.copySelection, icon)

		icon = QtGui.QIcon.fromTheme("edit-paste")

		self.paste = createAction(self, "Paste", "Ctrl+V", 'Paste text from clipboard.', self.pasteText, icon)

		icon = QtGui.QIcon.fromTheme("edit-find")

		self.find = createAction(self, "Find", "Ctrl+F", 'Find text.', self.findTextDialog, icon)

		editMenu = mainMenu.addMenu('Edit')
		editMenu.addAction(self.undo)
		editMenu.addAction(self.redo)
		editMenu.addSeparator()
		editMenu.addAction(self.copy)
		editMenu.addAction(self.paste)
		editMenu.addAction(self.clear)
		editMenu.addSeparator()
		editMenu.addAction(self.find)

		viewMenu = mainMenu.addMenu('View')

		icon = QtGui.QIcon.fromTheme("preferences-desktop-font")
		textSizeMenu = QtGui.QMenu('Font size', self)
		textSizeMenu.setIcon(icon)
		viewMenu.addMenu(textSizeMenu)

		self.size20 = createAction(self, "Huge", None, 'Change font size to 20px.', self.changeSizeTo20, None)
		self.size16 = createAction(self, "Large", None, 'Change font size to 16px.', self.changeSizeTo16, None)
		self.size12 = createAction(self, "Big", None, 'Change font size to 12px.', self.changeSizeTo12, None)
		self.size9 = createAction(self, "Normal", None, 'Change font size to 9px.', self.changeSizeTo9, None)
		self.size20.setCheckable(True)
		self.size16.setCheckable(True)
		self.size12.setCheckable(True)
		self.size9.setCheckable(True)
		self.size9.setChecked(True)

		self.customFontSize = createAction(self, "Custom", None, 'Choose custom font size.', self.setCustomFontSize, None)
		self.customFontSize.setCheckable(True)

		textSizeMenu.addAction(self.size9)
		textSizeMenu.addAction(self.size12)
		textSizeMenu.addAction(self.size16)
		textSizeMenu.addAction(self.size20)
		textSizeMenu.addSeparator()
		textSizeMenu.addAction(self.customFontSize)

		icon = QtGui.QIcon.fromTheme("help-about")

		self.help = createAction(self, "About", "Ctrl+H", 'Show About.', self.showHelp, icon)

		helpMenu = mainMenu.addMenu('Help')
		helpMenu.addAction(self.help)

		self.stateSpaceDirectory = "../Model/"
		self.reactionsDirectory = "../Model/"

		# setup

		#self.stateSpaceTime = QtCore.QTime(0,0,0,0)
		#self.reactionsTime = QtCore.QTime(0,0,0,0)

		#self.spaceTimer = QtCore.QTimer(self)
		#self.spaceTimer.timeout.connect(self.showStateProgress)

		#self.reactionsTimer = QtCore.QTimer(self)
		#self.reactionsTimer.timeout.connect(self.showReactionProgress)

		#self.stateSpaceEstimate = 0
		#self.reactionsEstimate = 0

		self.tabs = QTabWidget(self)
		self.tabs.move(605, 30)
		self.tabs.setMinimumSize(320, 430)

		self.tab1 = QWidget()
		self.tab2 = QWidget()
		self.tab3 = QWidget()

		self.tabs.addTab(self.tab1, "State space")
		self.tabs.addTab(self.tab2, "Model analysis")
		self.tabs.addTab(self.tab3, "Simulation")

		#########################################

		# text area

		self.textBox = QTextEdit(self)
		self.textBox.setMinimumSize(590, 430)
		self.textBox.move(10, 30)
		#self.textBox.cursorPositionChanged.connect(self.textEdited)
		self.textBox.setLineWrapColumnOrWidth(590)
		self.textBox.setLineWrapMode(QtGui.QTextEdit.FixedColumnWidth)

		self.highlighter = MyHighlighter( self.textBox )

		self.textBox.setText("# rules\n\n\n# initial state\n")

		self.oldPlainText = self.textBox.toPlainText()

		self.textBox.textChanged.connect(self.checkRules)
		self.textBox.textChanged.connect(self.checkRates)

		#########################################

		self.stateWorker = StateSpaceWorker(self.textBox)
		self.analysisWorker = AnalysisWorker(self.textBox, self.stateWorker)
		self.simulationWorker = SimulationWorker(self.textBox)

		#########################################

		vLayout = QVBoxLayout()

		# state space file button

		StatesHbox = QHBoxLayout()

		self.stateSpace = createButton(self, 'State space output file', self.save_stateSpace, False)
		self.stateSpace.setStatusTip("Choose file for storing state space.")

		StatesHbox.addWidget(self.stateSpace)

		self.stateSpace_text = createTextBox(self, None, None, True)

		StatesHbox.addWidget(self.stateSpace_text)

		vLayout.addLayout(StatesHbox)

		# Compute states button

		StatesHbox = QHBoxLayout()

		self.computeStateSpace_button = createButton(self, 'Compute', self.stateWorker.computeStateSpace, True)
		self.computeStateSpace_button.clicked.connect(self.progressbarStatesOnStart)
		self.computeStateSpace_button.setStatusTip("Compute state space of given model.")
		#self.computeStateSpace_button.clicked.connect(self.startStateSpaceTimer)

		self.cancel_state = createButton(self, 'Cancel', self.cancel_computation_states, True)
		self.cancel_state.setStatusTip("Cancel current computations.")
		self.cancel_state.clicked.connect(self.progressbarStatesOnFinished)
		self.cancel_state.clicked.connect(self.stateSpaceCanceled)

		StatesHbox.addWidget(self.cancel_state)
		StatesHbox.addWidget(self.computeStateSpace_button)

		vLayout.addLayout(StatesHbox)

		# progres bar

		StatesHbox = QHBoxLayout()

		self.progress_bar_states = createProgressBar(self)

		StatesHbox.addWidget(self.progress_bar_states)
		vLayout.addLayout(StatesHbox)

		self.stateWorker.taskFinished.connect(self.progressbarStatesOnFinished)
		self.stateWorker.showMostStates.connect(self.showNumberOfStates)
		self.stateWorker.NumOfStates.connect(self.updateNumOfStates)
		self.stateWorker.reactionsDone.connect(self.enableSaveReactions)

		# show graph

		StatesHbox = QHBoxLayout()

		self.display_graph_button = createButton(self, "Show graph", self.showGraph, True)
		self.display_graph_button.setStatusTip("Show interactive graph of current state space.")

		StatesHbox.addWidget(self.display_graph_button)

		vLayout.addLayout(StatesHbox)

		# num of states label

		StatesHbox = QHBoxLayout()

		self.emptySpaceHack = QtGui.QLabel(self)

		StatesHbox.addWidget(self.emptySpaceHack)
		vLayout.addLayout(StatesHbox)

		# save reactions

		StatesHbox = QHBoxLayout()

		self.save_reactions_button = createButton(self, 'Save reactions to file', self.save_reactions, True)
		self.save_reactions_button.setStatusTip("Save reactions generated from model to a file.")

		StatesHbox.addWidget(self.save_reactions_button)
		vLayout.addLayout(StatesHbox)

		# results fields

		StatesHbox = QHBoxLayout()

		style = '''QLineEdit {background-color: rgb(214, 214, 214); border: none ; }'''

		self.statistics = createTextBox(self, 'Statistics of the model', '''QLineEdit {border: none ; }''', True)

		StatesHbox.addWidget(self.statistics)
		vLayout.addLayout(StatesHbox)

		StatesHbox = QHBoxLayout()

		self.num_of_states = createTextBox(self, 'No. of States:'.ljust(30), style, True)

		StatesHbox.addWidget(self.num_of_states)
		vLayout.addLayout(StatesHbox)

		StatesHbox = QHBoxLayout()

		self.num_of_edges = createTextBox(self, 'No. of Edges:'.ljust(30), style, True)

		StatesHbox.addWidget(self.num_of_edges)
		vLayout.addLayout(StatesHbox)

		StatesHbox = QHBoxLayout()

		self.num_of_reactions = createTextBox(self, 'No. of Reactions:'.ljust(30), style, True)

		StatesHbox.addWidget(self.num_of_reactions)
		vLayout.addLayout(StatesHbox)

		self.tab1.setLayout(vLayout)

		# time bar

		#self.runningStates = QtGui.QLabel(self)
		#self.runningStates.setText(" Na:Na:Na /  Na:Na:Na")
		#self.runningStates.move(775, 155)

		#####################################################################################

		# dynamic analysis

		vLayout = QVBoxLayout()

		StatesHbox = QHBoxLayout()

		style = '''QLineEdit {background-color: rgb(214, 214, 214); border: none ; }'''

		self.reach_text = createTextBox(self, 'Reachability', '''QLineEdit {border: none ; font-weight: bold }''', True)

		StatesHbox.addWidget(self.reach_text)
		vLayout.addLayout(StatesHbox)

		# dynamical widgets for filling stuff

		self.scrollLayout = QtGui.QFormLayout()
		self.scrollLayout.setVerticalSpacing(0)
		#self.scrollLayout.setMargin(0)

		self.scrollWidget = QtGui.QWidget()
		self.scrollWidget.setLayout(self.scrollLayout)

		self.scrollArea = QtGui.QScrollArea()
		self.scrollArea.setWidgetResizable(True)
		self.scrollArea.setWidget(self.scrollWidget)

		vLayout.addWidget(self.scrollArea)

		self.addButton = QtGui.QPushButton('+')
		self.addButton.setStatusTip("Add another agent to be checked.")
		self.addButton.setMaximumWidth(25)
		self.addButton.clicked.connect(self.addDynamicWidget)

		self.scrollLayout.addRow(self.addButton)
		self.addButton.setDisabled(True)

		# progres bar

		StatesHbox = QHBoxLayout()

		self.progress_bar_reachability = createProgressBar(self)

		StatesHbox.addWidget(self.progress_bar_reachability)
		vLayout.addLayout(StatesHbox)

		# show result - message

		StatesHbox = QHBoxLayout()

		self.reachabilityResult = QtGui.QLabel(self)

		StatesHbox.addWidget(self.reachabilityResult)

		self.reachable_states_button = createButton(self, "Show results", self.showReachableStates, True)

		StatesHbox.addWidget(self.reachable_states_button)

		vLayout.addLayout(StatesHbox)

		# Compute reactions button

		StatesHbox = QHBoxLayout()

		self.compute_reachability_button = createButton(self, 'Check reachability', self.startReachability, True)
		self.compute_reachability_button.setStatusTip("Check whether chosen agents are reachable.")

		StatesHbox.addWidget(self.compute_reachability_button)

		vLayout.addLayout(StatesHbox)

		self.analysisWorker.reachFinished.connect(self.writeReachResult)


		#########################################

		# static analysis

		StatesHbox = QHBoxLayout()

		style = '''QLineEdit {background-color: rgb(214, 214, 214); border: none ; }'''

		self.reach_text = createTextBox(self, 'Static analysis', '''QLineEdit {border: none ; font-weight: bold }''', True)

		StatesHbox.addWidget(self.reach_text)
		vLayout.addLayout(StatesHbox)


		StatesHbox = QHBoxLayout()

		self.compute_conflicts = createButton(self, 'Compute conflicts', self.analysisWorker.compute_conflicts, True)
		self.compute_conflicts.setStatusTip("Apply static analysis for checking conflicts in given model.")

		StatesHbox.addWidget(self.compute_conflicts)

		vLayout.addLayout(StatesHbox)

		self.analysisWorker.noConflicts.connect(self.showConflicts)
		self.analysisWorker.conflicts.connect(self.showNoConflicts)


		StatesHbox = QHBoxLayout()

		self.noConflictsMessage = QtGui.QLabel(self)

		StatesHbox.addWidget(self.noConflictsMessage)
		vLayout.addLayout(StatesHbox)

		# result field

		self.tab2.setLayout(vLayout)

		# time bar

		# self.runningReactions = QtGui.QLabel(self)
		# self.runningReactions.setText(" Na:Na:Na /  Na:Na:Na")
		# self.runningReactions.move(775, 305)

		self.stateWorker.lenStates = self.num_of_states
		self.stateWorker.lenEdges = self.num_of_edges
		self.stateWorker.lenReactions = self.num_of_reactions

		#########################################

		vLayout = QVBoxLayout()

		StatesHbox = QHBoxLayout()

		self.maxTimeLabel = QtGui.QLabel(self)
		self.maxTimeLabel.setText("Maximum time:")
		StatesHbox.addWidget(self.maxTimeLabel)

		self.maxTimeEdit = QtGui.QLineEdit(self)
		StatesHbox.addWidget(self.maxTimeEdit)
		self.maxTimeEdit.textEdited.connect(self.updateSimulationMaxTime)

		self.unitInfo = QtGui.QLabel(self)
		self.unitInfo.setText("(in seconds)")
		StatesHbox.addWidget(self.unitInfo)

		self.step = 1

		vLayout.addLayout(StatesHbox)

		# -------------

		StatesHbox = QHBoxLayout()

		self.numberOfRunsLabel = QtGui.QLabel(self)
		self.numberOfRunsLabel.setText("Number of total runs:")
		StatesHbox.addWidget(self.numberOfRunsLabel)

		self.number_of_runs = QSpinBox()
		StatesHbox.addWidget(self.number_of_runs)
		self.number_of_runs.setRange(1, 20)
		self.number_of_runs.setValue(1)
		self.number_of_runs.valueChanged.connect(self.updateNumberOfRuns)

		vLayout.addLayout(StatesHbox)

		# -------------

		self.progress_bar_simulation = QProgressBar(self)
		self.progress_bar_simulation.setRange(0,100)

		vLayout.addWidget(self.progress_bar_simulation)

		# -------------

		StatesHbox = QHBoxLayout()

		self.cancel_simulation_button = createButton(self, 'Cancel', self.cancel_compute_simulation, True)
		self.cancel_simulation_button.setStatusTip("Cancel current computation of simulation.")

		StatesHbox.addWidget(self.cancel_simulation_button)

		self.compute_simulation_button = createButton(self, 'Simulate', self.simulationWorker.simulate, True)
		self.compute_simulation_button.setStatusTip("Simulate current model.")
		self.compute_simulation_button.clicked.connect(self.simulationStarted)

		StatesHbox.addWidget(self.compute_simulation_button)

		vLayout.addLayout(StatesHbox)

		vLayout.setAlignment(QtCore.Qt.AlignTop)  # might cause problems !
		self.tab3.setLayout(vLayout)

		#########################################

		self.simulationWorker.simulationFinished.connect(self.showPlot)
		self.simulationWorker.nextSecondCalculated.connect(self.updateSimulationProgress)

	def updateNumberOfRuns(self):
		self.simulationWorker.numberOfRuns = int(self.number_of_runs.value())
		maxTime = int(self.maxTimeEdit.text())
		if maxTime != 1:
			self.step = (100/(maxTime - 1))/self.simulationWorker.numberOfRuns

	def showPlot(self):
		self.maxTimeEdit.setReadOnly(False)
		self.compute_simulation_button.setDisabled(False)
		self.cancel_simulation_button.setDisabled(True)
		self.progress_bar_simulation.setValue(100)
		self.plot = SimulationPlot(self.simulationWorker.data, self.simulationWorker.times, self.simulationWorker.translations, self.screenWidth, self.screenHeight)

	def updateSimulationProgress(self):
		self.progress_bar_simulation.setValue(self.progress_bar_simulation.value() + self.step)

	def checkRates(self):
		if Import.checkRates(str(self.textBox.toPlainText())):
			if self.maxTimeEdit.text():
				self.compute_simulation_button.setDisabled(False)
		else:
			self.compute_simulation_button.setDisabled(True)

	def simulationStarted(self):
		self.progress_bar_simulation.reset()
		self.cancel_simulation_button.setDisabled(False)
		self.maxTimeEdit.setReadOnly(True)
		self.compute_simulation_button.setDisabled(True)

	def updateSimulationMaxTime(self):
		self.progress_bar_simulation.reset()
		if str(self.maxTimeEdit.text()).isdigit():
			maxTime = int(self.maxTimeEdit.text())
			if maxTime != 1:
				self.step = (100/(maxTime - 1))/self.simulationWorker.numberOfRuns
			self.simulationWorker.max_time = maxTime
			self.compute_simulation_button.setDisabled(False)
		else:
			self.compute_simulation_button.setDisabled(True)

	def cancel_compute_simulation(self):
		if not self.simulationWorker.TheWorker.wait(100):
			self.simulationWorker.TheWorker.terminate()
			self.compute_simulation_button.setDisabled(True)
			self.cancel_simulation_button.setDisabled(True)
			self.progress_bar_simulation.reset()

	def checkRules(self):
		noErroFormat = QtGui.QTextCharFormat()
		noErroFormat.setUnderlineStyle(QTextCharFormat.NoUnderline)

		if self.oldPlainText != self.textBox.toPlainText():
			self.oldPlainText = self.textBox.toPlainText()
			self.statusBar().clearMessage()
			self.rulesAreCorrect, error = Import.analyseRules(self.textBox.toPlainText())
			self.cursor = self.textBox.textCursor()
			self.cursor.setPosition(QTextCursor.Start)
			self.cursor.movePosition(QTextCursor.End, 1)
			self.cursor.mergeCharFormat(noErroFormat)

			if not self.rulesAreCorrect:
				errorFormat = QtGui.QTextCharFormat()
				errorFormat.setUnderlineStyle(QtGui.QTextCharFormat.WaveUnderline)
				errorFormat.setUnderlineColor(QtGui.QColor("red"))

				self.cursor.setPosition(error[0])
				for i in range(error[0], error[1]):
					self.cursor.movePosition(QtGui.QTextCursor.NextCharacter, 1)
				self.cursor.mergeCharFormat(errorFormat)

				self.statusBar().showMessage(self.tr(error[2]))
				self.computeStateSpace_button.setDisabled(True)
			elif self.stateWorker.stateSpaceFile:
				self.computeStateSpace_button.setDisabled(False)

	def setCustomFontSize(self):
		self.customFontSize.setChecked(True)
		self.fontSize = FontSize(self)
		self.fontSize.show()

	def changeSizeTo9(self):
		self.size9.setChecked(True)
		self.changeFontSize(9)
		self.size12.setChecked(False)
		self.size16.setChecked(False)
		self.size20.setChecked(False)
		self.customFontSize.setChecked(False)

	def changeSizeTo12(self):
		self.size12.setChecked(True)
		self.changeFontSize(12)
		self.size9.setChecked(False)
		self.size16.setChecked(False)
		self.size20.setChecked(False)
		self.customFontSize.setChecked(False)

	def changeSizeTo16(self):
		self.size16.setChecked(True)
		self.changeFontSize(16)
		self.size12.setChecked(False)
		self.size9.setChecked(False)
		self.size20.setChecked(False)
		self.customFontSize.setChecked(False)

	def changeSizeTo20(self):
		self.size20.setChecked(True)
		self.changeFontSize(20)
		self.size12.setChecked(False)
		self.size16.setChecked(False)
		self.size9.setChecked(False)
		self.customFontSize.setChecked(False)

	def changeFontSize(self, size):
		cursor = self.textBox.textCursor()
		self.textBox.selectAll()
		self.textBox.setFontPointSize(size)
		self.textBox.setTextCursor(cursor)

	def showGraph(self):
		useHTMLvisual = True
		#if len(self.stateWorker.states) > 100:
		#	useHTMLvisual = False
		self.graph = GraphVisual(self.stateWorker.stateSpaceFile, self.screenWidth - 100, self.screenHeight - 100, useHTMLvisual)

	def showReachableStates(self):
		self.graphReach = ReachableGraphVisual(self.stateWorker.stateSpaceFile, self.screenWidth - 100, self.screenHeight - 100, self.analysisWorker.satisfyingStates)

	def resetReachIndicators(self):
		self.progress_bar_reachability.reset()
		self.reachabilityResult.setText("")
		#self.reachable_states_button.setDisabled(True)

	def writeReachResult(self):
		if self.analysisWorker.reachablityResult:
			self.reachabilityResult.setText("Reachable !")
			self.reachable_states_button.setDisabled(False)
		else:
			self.reachabilityResult.setText("Not reachable !")
		self.reachabilityResult.setStyleSheet("color: rgb(0, 155, 0);")

	def startReachability(self):
		self.progress_bar_reachability.setRange(0,0)
		checkWheterReachable = True
		orderedAgents = self.stateWorker.uniqueAgents
		vector = [0] * len(orderedAgents)

		if self.checkAgentFields():
			if self.checkStochiometryFields():
				if self.checkExistanceOfAgents(orderedAgents):
					for i in range(self.scrollLayout.count() - 1):
						widget = self.scrollLayout.itemAt(i).widget()
						agent = str(widget.agent.text())
						stochio = str(widget.stochio.text())
						vector[orderedAgents.index(agent)] = int(stochio)
					self.analysisWorker.toBeReached = np.array(vector)
					self.analysisWorker.compute_reach()

		self.progress_bar_reachability.setRange(0,1)
		self.progress_bar_reachability.setValue(1)

	def checkAgentFields(self):
		for i in range(self.scrollLayout.count() - 1):
			widget = self.scrollLayout.itemAt(i).widget()
			agent = str(widget.agent.text())
			if not agent:
				self.reachabilityResult.setText("No agent given !")
				self.reachabilityResult.setStyleSheet("color: rgb(255, 0, 0);")
				widget.agent.setStyleSheet("background-color : rgb(255, 0, 0);")
				return False
		return True

	def checkStochiometryFields(self):
		for i in range(self.scrollLayout.count() - 1):
			widget = self.scrollLayout.itemAt(i).widget()
			stochio = str(widget.stochio.text())
			if not stochio.isdigit():
				self.reachabilityResult.setText("Wrong stochiometry !")
				self.reachabilityResult.setStyleSheet("color: rgb(255, 0, 0);")
				widget.stochio.setStyleSheet("color: rgb(255, 0, 0);")
				return False
		return True

	def checkExistanceOfAgents(self, orderedAgents):
		for i in range(self.scrollLayout.count() - 1):
			widget = self.scrollLayout.itemAt(i).widget()
			agent = str(widget.agent.text())
			if agent not in orderedAgents:
				self.reachabilityResult.setText("Not reachable !")
				self.reachabilityResult.setStyleSheet("color: rgb(0, 155, 0);")
				return False
		return True

	def checkScrollArea(self):
		self.reachable_states_button.setDisabled(True)
		if self.getRowDeleted():
			if self.scrollLayout.count() < 3:
				self.compute_reachability_button.setDisabled(True)
			self.setRowDeleted("0")

	def setRowDeleted(self, value):
		self.rowDeleted.setText(value)

	def getRowDeleted(self):
		return bool(int(str(self.rowDeleted.text())))

	def addDynamicWidget(self):
		self.resetReachIndicators()
		self.addButton.deleteLater()
		self.scrollLayout.addRow(FillAgentToBeFound(self.stateWorker.uniqueAgents, self))

		self.addButton = QtGui.QPushButton('+')
		self.addButton.setMaximumWidth(25)
		self.addButton.clicked.connect(self.addDynamicWidget)

		self.scrollLayout.addRow(self.addButton)

		# no idea why it is working like this:
		self.scrollArea.verticalScrollBar().setMaximum(self.scrollArea.verticalScrollBar().maximum() + 45)
		self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
		# but its working tho..

		self.compute_reachability_button.setDisabled(False)

	def showConflicts(self):
		self.noConflictsMessage.setText("")
		self.window = DisplayConflicts(self.analysisWorker.message[:-22])
		self.window.show()

	def showNoConflicts(self):
		self.noConflictsMessage.setText("No conflicts !")

	def updateNumOfStates(self):
		return
		#self.numCurrentOfStates.setText(str(self.stateWorker.numOfCurrentStates))

	def showNumberOfStates(self):
		return
		#self.numOfStates.setText(" / " + str(self.stateWorker.mostNumberOfStates))

	def startStateSpaceTimer(self):
		self.spaceTimer.start(1000)
		self.stateSpaceEstimate = time.strftime("%H:%M:%S", time.gmtime(Gen.estimateComputation(3, 10, 10)))

	def stateReactionsTimer(self):
		self.reactionsTimer.start(1000)
		self.reactionsEstimate = time.strftime("%H:%M:%S", time.gmtime(Implicit.estimateComputation(10)))

	def stateSpaceCanceled(self):
		self.num_of_states.setText('No. of States:'.ljust(30) + 'n\\a' )
		self.num_of_edges.setText('No. of Edges:'.ljust(30) + 'n\\a' )
		self.num_of_reactions.setText('No. of Reactions:'.ljust(30) + 'n\\a' )
		self.progress_bar_states.setValue(0)
		self.addButton.setDisabled(True)
		self.display_graph_button.setDisabled(True)

		#self.spaceTimer.stop()

	def enableSaveReactions(self):
		self.save_reactions_button.setDisabled(False)

	def progressbarStatesOnStart(self): 
		self.progress_bar_states.setRange(0,0)
		self.cancel_state.setDisabled(False)

	def progressbarStatesOnFinished(self):
		self.progress_bar_states.setRange(0,1)
		self.progress_bar_states.setValue(1)
		self.cancel_state.setDisabled(True)
		self.addButton.setDisabled(False)
		self.display_graph_button.setDisabled(False)

	def open_model(self):
		file = QFileDialog.getOpenFileName(self, 'Choose model', directory = '../Examples/', filter ="BCS (*.bcs);;All types (*)")
		if file:
			file = open(file, "r")
			self.textBox.setPlainText(file.read())
			self.compute_conflicts.setDisabled(False)
			if self.stateWorker.stateSpaceFile and self.rulesAreCorrect:
				self.computeStateSpace_button.setDisabled(False)

	def load_state_space(self):
		file = QFileDialog.getOpenFileName(self, 'Choose file', filter ="JSON (*.json);;All types (*)")
		if file:
			self.stateWorker.stateSpaceFile = file
			self.stateSpace_text.setText(self.stateWorker.stateSpaceFile)
			self.display_graph_button.setDisabled(False)
			return True
		return False

	def save_stateSpace(self):
		file = QFileDialog.getSaveFileName(self, 'Choose output file', directory = self.stateSpaceDirectory, filter =".json (*.json);;All types (*)")
		if file:
			self.stateSpaceDirectory = os.path.dirname(str(file))
			if not os.path.splitext(str(file))[1]:
				file = str(file) + ".json"
			self.stateWorker.stateSpaceFile = file
			self.stateSpace_text.setText(self.stateWorker.stateSpaceFile)
			if self.stateWorker.modelFile and self.rulesAreCorrect:
				self.computeStateSpace_button.setDisabled(False)

	def save_reactions(self):
		file = QFileDialog.getSaveFileName(self, 'Choose log file', directory = self.reactionsDirectory, filter =".txt (*.txt);;All types (*)")
		if file:
			self.reactionsDirectory = os.path.dirname(str(file))
			if not os.path.splitext(str(file))[1]:
				file = str(file) + ".txt"
			f = open(file,'w')
			f.write("\n".join(self.stateWorker.reactions))
			f.close()

	def cancel_computation_states(self):
		if not self.stateWorker.TheWorker.wait(100):
			self.stateWorker.TheWorker.terminate()
			self.computeStateSpace_button.setDisabled(True)
			self.cancel_state.setDisabled(True)
			self.stateSpace.setDisabled(True)

	def showStateProgress(self):
		self.stateSpaceTime = self.stateSpaceTime.addSecs(1)
		text = self.stateSpaceTime.toString('hh:mm:ss')
		#self.runningStates.setText(text + " / " + self.stateSpaceEstimate)
		
	def save_model(self):
		file = QFileDialog.getSaveFileName(self, 'Choose model file', filter ="BCS (*.bcs);;All types (*)")
		if file:
			if not os.path.splitext(str(file))[1]:
				file = str(file) + ".bcs"
			with open(file, 'w') as file:
				file.write(self.textBox.toPlainText())

	def copySelection(self):
		self.textBox.copy()

	def pasteText(self):
		self.textBox.paste()

	def clearText(self):
		self.textBox.clear()

	def undoText(self):
		self.textBox.undo()

	def redoText(self):
		self.textBox.redo()

	def findTextDialog(self):
		self.textBox.moveCursor(QTextCursor.Start)
		findDialog = Find(self)
		findDialog.show()

	def findTheText(self, text):
		wasFound = self.textBox.find(text)
		if not wasFound:
			self.textBox.moveCursor(QTextCursor.Start)
			self.textBox.find(text)

	def showHelp(self):
		self.help = Help()

	def importStateSpace(self):
		if self.load_state_space():
			self.stateWorker.states, self.stateWorker.edges, self.stateWorker.uniqueAgents = Import.importStateSpace(self.stateWorker.stateSpaceFile)
			self.addButton.setDisabled(False)

	def resizeEvent(self, event):
		widthShrint = self.width() - appWidth
		heightShrink = self.height() - appHeight 
		self.textBox.resize(590 + widthShrint, 430 + heightShrink)
		self.tabs.move(605 + widthShrint, 30)
		self.tabs.resize(320, 430 + heightShrink)

	def quitThreads(self):
		self.analysisWorker.TheWorker.quit()
		self.analysisWorker.TheWorker.wait()
		self.stateWorker.TheWorker.quit()
		self.stateWorker.TheWorker.wait()
		self.simulationWorker.TheWorker.quit()
		self.simulationWorker.TheWorker.wait()

def handleIntSignal(signum, frame):
	"""Handler for the SIGINT signal.
	sends Exit Code Number 130 'Script terminated by Control-C' 
	Control-C is fatal error signal 2, (130 = 128 + signal 'n') """
	main.quitThreads()
	sys.exit()

signal.signal(signal.SIGINT, handleIntSignal)

app = QtGui.QApplication(sys.argv)

app_icon = QtGui.QIcon()
app_icon.addFile('icons/16x16.png', QtCore.QSize(16,16))
app_icon.addFile('icons/24x24.png', QtCore.QSize(24,24))
app_icon.addFile('icons/32x32.png', QtCore.QSize(32,32))
app_icon.addFile('icons/48x48.png', QtCore.QSize(48,48))
app_icon.addFile('icons/128x128.png', QtCore.QSize(128,128))
app.setWindowIcon(app_icon)

screen_rect = app.desktop().screenGeometry()
screenWidth, screenHeight = screen_rect.width(), screen_rect.height()

appWidth = 930
appHeight = 485

main = MainWindow(screenWidth, screenHeight)
main.setMinimumSize(appWidth, appHeight)
main.setWindowTitle('BCSgen')
main.show()

app.exec_()
try:
	os.remove("graphReach.html")
	os.remove("graph.html")
	os.remove("graph.svg")
except OSError:
	pass

main.quitThreads()

sys.exit()