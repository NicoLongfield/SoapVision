from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

import sys
from pathlib import Path
import time
import os
import json

import asyncio
import concurrent.futures
import threading
import multiprocessing
import math
import serial

from collections import deque
import pyqtgraph as pg

import cv2
import numpy as np

from tracker import *
from OPC_UA import *
from Time_func import *
from csi_camera import CSI_Camera
from cam import *



# SAVON = sys.argv[2]

time_init()
print(OPCUA_Pause)
# print(SAVON)



class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def tickStrings(self, values, scale, spacing):
        return [int2dt(value).strftime("%H:%M:%S.%f") for value in values]


class Arduiuno_Comm(QThread):
    change_json_serial_comm = pyqtSignal(dict)


    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.arduino = serial.Serial(
        port = '/dev/ttyACM0',
        baudrate = 115200,
        bytesize = serial.EIGHTBITS,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        timeout = 0,
        xonxoff = False,
        rtscts = False,
        dsrdtr = False,
        writeTimeout = 2
        )
        self.arduino.reset_input_buffer()
    @pyqtSlot(dict)
    def run(self):
        while self._run_flag:
            data = self.arduino.readline().decode("utf-8")
            try:
                dict_json = json.loads(data)
                self.change_json_serial_comm.emit(dict_json)
            except json.JSONDecodeError as e:
                dict_json = {}
            time.sleep(0.01)
    
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False

class MyWindow(QMainWindow):
    thread = VideoThread()
    thread2 = Arduiuno_Comm()
    thread_test = VideoThread_Zoom()
    def __init__(self):
        super(MyWindow, self).__init__()
        # self.available_cameras = QCameraInfo.availableCameras()  # Getting available cameras
        
       

        cent = QDesktopWidget().availableGeometry().center()  # Finds the center of the screen
        self.setStyleSheet("background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1, stop:0 rgb(35, 35, 45), stop:1  rgb(3, 3, 25));")
        self.resize(1900, 1050)
        self.frameGeometry().moveCenter(cent)
        self.setWindowTitle('S O A P V I S I O N')
        self.initWindow()
        self.ClickStartTestZoom()
        self.ss_video.setEnabled(False)
        
########################################################################################################################
#                                                   Windows                                                            #
########################################################################################################################
    def initWindow(self):
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        self.font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)


        # create the video capture thread

        self.checkbox_recyclage = QCheckBox(self)
        self.checkbox_recyclage.move(1435, 135)
        self.checkbox_recyclage.resize(400, 35)
        self.checkbox_recyclage.setText("Activer/Désactiver recyclage auto.")
        self.checkbox_recyclage.setFont(self.font)
        self.checkbox_recyclage.setStyleSheet("QCheckBox::indicator{width: 30px; height: 30px; color: white;}QCheckBox{color: white; background-color: rgba(35,35,45,255);}")
        # self.thread_test = VideoThread_Zoom()

        self.label_color = QLabel(self)
        self.label_color.move(1685, 320)
        self.label_color.resize(120,120)
        # self.label_color.setAutoFillBackground(True)
        self.color_r = 0
        self.color_g = 0
        self.color_b = 0
        self.color_lux = 0
        self.temp = 0
        self.hum = 0
        self.data_temp = deque(maxlen=40)
        self.data_hum = deque(maxlen=40)
        self.data_time = deque(maxlen=40)
        self.label_color.setStyleSheet("border: 3px black; border-radius: 50px; background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))

        self.label_data = QLabel(self)

        self.label_data.setStyleSheet("background-color: rgba(255,255,255,0); color: white;")
        self.label_data.setFont(self.font)
        self.label_data.setText('Données des capteurs : \n R = {} \t G = {} \t B = {} \t Lux = {} \n Temp Celsius = {} \t Hum = {} \n'.format(self.color_r, self.color_g, self.color_b, self.color_lux, self.temp, self.hum))
        self.label_data.move(1435, 300)
        self.label_data.adjustSize()
        self.label_data.setAlignment(Qt.AlignLeft)

        self.thread2.change_json_serial_comm.connect(self.update_text)
        self.thread2.start()


        self.label = QLabel(self)  # Create label
        self.label.setText('SoapVision : Application de vision numérique pour la mini-usine')  # Add text to label
        self.label.setFont(self.font)
        self.label.setStyleSheet("background-color: rgba(255,255,255,0); color: white;")
        self.label.move(15, 980)  
        self.label.resize(850, 40)  
        self.label.setAlignment(Qt.AlignLeft) 

        # Button to start video
        self.ss_video = QPushButton(self)
        self.ss_video.setText('Start video')
        self.ss_video.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.ss_video.setFont(self.font)
        self.ss_video.move(1435, 10)
        self.ss_video.resize(200, 75)
        self.ss_video.clicked.connect(self.ClickStartVideo)
        
        #ComboBox to select soap type
        self.combo = QComboBox(self)
        self.combo.setFont(self.font)
        self.combo.setStyleSheet("color: white;")
        self.combo.addItem("Orange")
        self.combo.addItem("Bleu")
        self.combo.addItem("Vert")
        self.combo.move(1435, 95)
        self.combo.resize(400, 35)
        # self.qlabel = QLabel(self)
        # self.qlabel.move(1500, 61)
        self.combo.activated[str].connect(self.onChanged)

        self.btn_test_zoom = QPushButton(self)
        self.btn_test_zoom.setText('Test Cam Zoom')
        self.btn_test_zoom.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.btn_test_zoom.setFont(self.font)
        self.btn_test_zoom.move(1645, 10)
        self.btn_test_zoom.resize(200, 75)
        self.btn_test_zoom.clicked.connect(self.ClickStartTestZoom)

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet("background : lightblue;")  # Setting style sheet to the status bar
        self.setStatusBar(self.status)  # Adding status bar to the main window
        self.status.showMessage('Ready to start')

        self.graph_widget = QFrame(self)
        self.graph_widget.move(55, 590)
        self.graph_widget.resize(760, 385)
        self.graph_widget.setStyleSheet("background-color: black")
        self.plt = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        self.plt.showGrid(x=True, y=True)
        self.plt.addLegend()
        self.plt.setLabel('left', 'Temp/Hum', units='y')
        self.plt.setLabel('bottom', 'Temps', units='s')
        # self.plt.setXRange(0, len(x))
		# self.plt.setYRange(0, max(y))
        self.line1 = self.plt.plot(x=list(self.data_time), y=list(self.data_hum), pen='g', symbol='x', symbolPen='g', symbolBrush=0.2, name='Hum')
        self.line2 = self.plt.plot(x=list(self.data_time), y=list(self.data_temp), pen='b', symbol='o', symbolPen='b', symbolBrush=0.2, name='Temp')
        self.graph_layout = QHBoxLayout(self)
        self.graph_widget.setLayout(self.graph_layout)
        self.graph_layout.addWidget(self.plt)
        
        self.image_label = QLabel(self)
        self.disply_width = 760
        self.display_height = 570
        self.image_label.resize(self.disply_width, self.display_height)
        self.image_label.setStyleSheet("background : black;")
        self.image_label.move(55, 10)

        self.image_label_zoom = QLabel(self)
        self.disply_width_zoom = 600
        self.display_height_zoom = 450
        self.image_label_zoom.resize(self.disply_width_zoom, self.display_height_zoom)
        self.image_label_zoom.setStyleSheet("background : black;")
        self.image_label_zoom.move(825, 10)

########################################################################################################################
#                                                   Buttons                                                            #
########################################################################################################################
    def onChanged(self, text):
        self.thread.type_savon = text
        self.thread_test.type_savon = text
        
        # self.qlabel.adjustSize()
    
    
    # Activates when Start/Stop video button is clicked to Start (ss_video
    def ClickStartVideo(self):
        # Change label color to light blue
        if self.thread_test.isRunning():
            self.btn_test_zoom.click()
        self.btn_test_zoom.setEnabled(False)
        self.ss_video.clicked.disconnect(self.ClickStartVideo)
        self.status.showMessage('Video Running...')
        # Change button to stop
        
            
        
        self.ss_video.setText('Stop video')
        self.ss_video.setStyleSheet("background-color: rgb(255, 80, 80);")
        # self.thread = VideoThread()
        self.thread.change_pixmap_signal_wide_view.connect(self.update_image)
        self.thread.change_pixmap_signal_zoom_view.connect(self.update_image_zoom, Qt.QueuedConnection)
        # start the thread
        self.thread.start()
        self.ss_video.clicked.connect(self.thread.stop)  # Stop the video if button clicked
        self.ss_video.clicked.connect(self.ClickStopVideo)


    # Activates when Start/Stop video button is clicked to Stop (ss_video)
    def ClickStopVideo(self):
        self.btn_test_zoom.setEnabled(True)
        self.thread.change_pixmap_signal_wide_view.disconnect()
        self.ss_video.setText('Start video')
        self.ss_video.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.status.showMessage('Ready to start')
        self.ss_video.clicked.disconnect(self.ClickStopVideo)
        self.ss_video.clicked.disconnect(self.thread.stop)
        self.ss_video.clicked.connect(self.ClickStartVideo)
        
    def ClickStartTestZoom(self):
        # Change label color to light blue
        if self.thread.isRunning():
            self.ss_video.click()
        self.ss_video.setEnabled(False)
        self.btn_test_zoom.clicked.disconnect(self.ClickStartTestZoom)
            
        # Change button to stop
        self.btn_test_zoom.setText('Stop Test Zoom')
        self.btn_test_zoom.setStyleSheet("background-color: rgb(255, 80, 80);")
        
        self.thread_test.change_pixmap_signal_test_zoom_view.connect(self.update_image)
      
        # start the thread
        self.thread_test.start()
        self.btn_test_zoom.clicked.connect(self.thread_test.stop)  # Stop the video if button clicked
        self.btn_test_zoom.clicked.connect(self.ClickStopTestZoom)


    # Activates when Start/Stop video button is clicked to Stop (ss_video)
    def ClickStopTestZoom(self):
        if self.ss_video.isEnabled() == False:
            self.ss_video.setEnabled(True)
        self.thread_test.change_pixmap_signal_test_zoom_view.disconnect()
        self.btn_test_zoom.setText('Start Test Zoom')
        self.btn_test_zoom.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.btn_test_zoom.clicked.disconnect(self.ClickStopTestZoom)
        self.btn_test_zoom.clicked.disconnect(self.thread_test.stop)
        self.btn_test_zoom.clicked.connect(self.ClickStartTestZoom)

########################################################################################################################
#                                                   Actions                                                            #
########################################################################################################################

    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def update_image_zoom(self, cv_img2):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt_zoom(cv_img2)
        self.image_label_zoom.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        #p = convert_to_Qt_format.scaled(801, 801, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def convert_cv_qt_zoom(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width_zoom, self.display_height_zoom, Qt.KeepAspectRatio)
        #p = convert_to_Qt_format.scaled(801, 801, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def update_text(self, str_json):
    # self.label.setText(json.dumps(str_json))
        if "R" in str_json:
            self.color_r = str_json["R"]
            self.color_g = str_json["G"]
            self.color_b = str_json["B"]
            self.color_lux = str_json["lux"]
            self.temp = str_json["dht_temp"]
            self.hum = str_json["dht_hum"]
        self.label_color.setStyleSheet("border: 5px black; border-radius: 60px; background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))
        self.label_data.setText('Donnees des capteurs : \n R = {} \n G = {} \n B = {} \n Lux = {} \n Temp Celsius = {} \n Hum = {} \n'.format(self.color_r, self.color_g, self.color_b, self.color_lux, self.temp, self.hum))
        self.label_data.adjustSize()
        self.data_temp.append(self.temp)
        self.data_hum.append(self.hum)
        self.data_time.append(time.time())
        self.update_graph()
        
    def update_graph(self):
        self.line1.setData(x=list(self.data_time), y=list(self.data_hum))#, pen='g', symbol='x',symbolPen='g', symbolBrush=0.2, name='Hum')
        self.line2.setData(x=list(self.data_time), y=list(self.data_temp))#, pen='b', symbol='o',symbolPen='b', symbolBrush=0.2, name='Temp')


    def closeEvent(self, event):
        self.thread2.stop()
        if (self.thread.isRunning() == True) or (self.thread_test.isRunning() == True):
            event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec())