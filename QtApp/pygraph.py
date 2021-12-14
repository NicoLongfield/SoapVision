# importing Qt widgets
from PyQt5.QtWidgets import *
import sys

# importing pyqtgraph as pg
import pyqtgraph as pg
from PyQt5.QtGui import *

from PyQt5.QtCore import Qt


# Bar Graph class
class BarGraphItem(pg.BarGraphItem):

	# constructor which inherit original
	# BarGraphItem
	def __init__(self, *args, **kwargs):
		pg.BarGraphItem.__init__(self, *args, **kwargs)

	# creating a mouse double click event
	def mouseDoubleClickEvent(self, e):

		# setting scale
		self.setScale(0.2)


class Window(QMainWindow):

	def __init__(self):
		super().__init__()

		# setting title
		self.setWindowTitle("PyQtGraph")

		# setting geometry
		self.setGeometry(100, 100, 600, 500)

		# icon
		icon = QIcon("skin.png")

		# setting icon to the window
		self.setWindowIcon(icon)

		# calling method
		self.UiComponents()

		# showing all the widgets
		self.show()
        
	# method for components
    def UiComponents(self):
        widget = QWidget()

		label = QLabel("Données des capteurs")
		# making it multiline
		label.setWordWrap(True)
		# y values to plot by line 1
		y = []

		# y values to plot by line 2
		y2 = []
		x = []

		# create plot window object
		plt = pg.plot()

		# showing x and y grids
		plt.showGrid(x=True, y=True)

		# adding legend
		plt.addLegend()

		# set properties of the label for y axis
		plt.setLabel('left', 'Temp/Hum', units='y')

		# set properties of the label for x axis
		plt.setLabel('bottom', 'Temps', units='s')

		# setting horizontal range
		plt.setXRange(0, len(x))

		# setting vertical range
		plt.setYRange(0, max(y))

		# ploting line in green color
		# with dot symbol as x, not a mandatory field
		line1 = plt.plot(x, y, pen='g', symbol='x',
						symbolPen='g', symbolBrush=0.2, name='Temp')

		# ploting line2 with blue color
		# with dot symbol as o
		line2 = plt.plot(x, y2, pen='b', symbol='o',
						symbolPen='b', symbolBrush=0.2, name='Hum')

		# setting X pos to the line1
		line1.setX(-2)

		# setting Y pos of line 1
		line1.setY(5)

		# getting X & Y pos of line 1
		valuex = line1.x()
		valuey = line1.y()

		# setting text to the label
		label.setText("X & Y pos : " + str(valuex) + ", " + str(valuey))

		# label minimum width
		label.setMinimumWidth(120)

		# Creating a grid layout
		layout = QGridLayout()

		# setting this layout to the widget
		widget.setLayout(layout)

		# adding label to the layout
		layout.addWidget(label, 1, 0)

		# plot window goes on right side, spanning 3 rows
		layout.addWidget(plt, 0, 1, 3, 1)

		# setting this widget as central widget of the main window
		self.setCentralWidget(widget)


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
window = Window()

# start the app
sys.exit(App.exec())

# from PyQt5 import QtGui, QtWidgets # (the example applies equally well to PySide2)
# from PyQt5.QtWidgets import QWidget, QApplication, QLineEdit, QListWidget, QPushButton
# import pyqtgraph as pg

# ## Always start by initializing Qt (only once per application)
# app = QApplication([])

# ## Define a top-level widget to hold everything
# w = QtWidgets([])

# ## Create some widgets to be placed inside
# btn = w.QPushButton('press me')
# text = w.QLineEdit('enter text')
# listw = w.QListWidget()
# plot = pg.PlotWidget()

# ## Create a grid layout to manage the widgets size and position
# layout = QWidget.QGridLayout()
# w.setLayout(layout)

# ## Add widgets to the layout in their proper positions
# layout.addWidget(btn, 0, 0)   # button goes in upper-left
# layout.addWidget(text, 1, 0)   # text edit goes in middle-left
# layout.addWidget(listw, 2, 0)  # list widget goes in bottom-left
# layout.addWidget(plot, 0, 1, 3, 1)  # plot goes on right side, spanning 3 rows

# ## Display the widget as a new window
# w.show()

# ## Start the Qt event loop
# app.exec_()