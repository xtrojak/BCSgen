from PyQt4 import QtGui, QtCore
import sys
import os.path
import numpy as np

sys.path.append(os.path.abspath('../../Core/'))
import Import as Import

class ImportWorker(QtCore.QObject):
	modelCorrect = QtCore.pyqtSignal()
	syntaxErrors = QtCore.pyqtSignal()
	notEnoughRates = QtCore.pyqtSignal()
	reactionsDone = QtCore.pyqtSignal()

	def __init__(self, model, parent = None):
		QtCore.QObject.__init__(self, parent)

		self.model = model
		self.oldPlainText = ""

		self.reactions = []
		self.rates = []
		self.init_state = []
		self.message = []
		self.isOK = False
		self.enoughRates = False

		self.TheWorker = QtCore.QThread()
		self.moveToThread(self.TheWorker)
		self.TheWorker.start()

	def analyseModel(self):
		if self.modelUpdated():
			rules, self.init_state, rates = Import.import_rules(self.model.toPlainText())
			if len(rules) != len(rates):
				self.notEnoughRates.emit()
				self.enoughRates = False
			else:
				self.enoughRates = True

			# would be fine to check initial state too
			self.message, self.isOK = Import.verifyRules(rules)

			if self.isOK:
				self.reactions, self.rates = Import.computeReactions(rules, rates)
				self.reactionsDone.emit()
				self.modelCorrect.emit()
			else:
				self.syntaxErrors.emit()

	def modelUpdated(self):
		if self.oldPlainText != self.model.toPlainText():
			self.oldPlainText = self.model.toPlainText()
			return True
		return False