from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from matplotlib.backends.backend_qt5agg import FigureCanvasQtAgg as FigureCanvas

class myApp(QWidget):
    def __init__(self):
        super().__init__()
        self.window_width, self.window_height = 1200, 800
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.input = QLineEdit()
        layout.addWidget(self.canvas)

        self.canvas = FigureCanvas(plt.Figure(figsize=(15,6)))
        layout.addWidget(self.canvas)

    def insert_ax(self):
        self.ax = self.canvas.figure.subplots()
        self.ax.set_ylim([0,100])
        self.ax.set_xlim([0,1])
        self.bar = self.canvas.figure.subplots()




if __name__=='__main__':
    app = QApplication(sys.argv)
    myApp = myApp()
    myApp.show()

    try:
        sys.exit(app.exec__())
    except SystemExit:
        print('Closing Window...')