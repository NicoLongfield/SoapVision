from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer

from PIL.ImageQt import ImageQt

import sys
from pathlib import Path
import time
import os
import json

import asyncio
import asyncua
import concurrent.futures
import threading
import multiprocessing
import math
import serial


from collections import deque
import pyqtgraph as pg

import cv2
import numpy as np

from csv_ import *
from tracker import *
from OPC_UA import *
from Time_func import *
from csi_camera import CSI_Camera
from cam import *
# from SegCNN import *

import logging

# SAVON = sys.argv[2]

time_init()
print(OPCUA_Pause)
# print(SAVON)



class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def tickStrings(self, values, scale, spacing):
        return [int2dt(value).strftime("%H:%M:%S.%f") for value in values]


class Slider(QSlider):
    def __init__(self, min_, max_, action):
        super().__init__(Qt.Horizontal)
        self.resize(400, 15)
        self.setMinimum(min_)
        self.setMaximum(max_)
        # self.setInvertedAppearance(True)
        self.setStyleSheet("QSlider::add-page:horizontal{background-color:white;} QSlider::sub-page:horizontal{background-color: white;}")
        self.valueChanged.connect(action)#self))


class Label_Slider(QLabel):
    def __init__(self, text, font):#, x, y):
        super().__init__()
        self.setText(text)
        self.resize(400,15)
        self.setStyleSheet("background-color: rgba(255,255,255,0); color: white;")
        self.setFont(font)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # self.move(x, y)
  


class Arduiuno_Comm(QThread):
    change_json_serial_comm = pyqtSignal(dict)


    def __init__(self):
        super().__init__()
        self._run_flag = True

    @pyqtSlot(dict)
    def run(self):
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
        while self._run_flag:
            data = self.arduino.readline().decode("utf-8")
            try:
                dict_json = json.loads(data)
                self.change_json_serial_comm.emit(dict_json)
            except json.JSONDecodeError as e:
                dict_json = {}
            time.sleep(0.01)
    
    def stop(self):
        """Sets run flag to False and waits for thread to  finish"""
        self._run_flag = False

class MyWindow(QMainWindow):
    thread = VideoThread()
    thread2 = Arduiuno_Comm()
    thread_test = VideoThread_Zoom()
    CSV = csv_data_export() #headers = ['Time', 'Image', 'Mask', 'Valid', 'Temp', 'Hum', 'Lux', 'R', 'G', 'B']
    # thread_ai = SegNet()
    
    def __init__(self):
        super(MyWindow, self).__init__()
        # self.available_cameras = QCameraInfo.availableCameras()  # Getting available cameras
        self.state_hsv = "Auto"
        self.type_savon = "Orange"
        self.image_name = ""
        self.mask_name = ""
        self.csv_enabled = True

        cent = QDesktopWidget().availableGeometry().center()  # Finds the center of the screen
        self.setStyleSheet("background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1, stop:0 rgb(35, 35, 45), stop:1  rgb(3, 3, 25));")
        self.resize(1900, 1050)
        self.frameGeometry().moveCenter(cent)
        self.setWindowTitle('S O A P V I S I O N')
        self.initWindow()
        self.ClickStartTestZoom()
        self.ss_video.setEnabled(False)
        #self.thread_ai.set()
        
        # self.thread_ai.start(priority=5)
        
########################################################################################################################
#                                                   Windows                                                            #
########################################################################################################################
    def initWindow(self):
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        self.font3 = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
        self.font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
        self.font2 = QtGui.QFont("Arial", 18, QtGui.QFont.Bold)



        self.label_resultat = QLabel(self)

        self.label_resultat.setStyleSheet("background-color: rgba(35,35,45,20); border: white; color: white;")
        self.label_resultat.setFont(self.font2)
        self.label_resultat.setText('Analyse IA :')
        self.label_resultat.move(780, 470)
        self.label_resultat.resize(600, 35)
        self.label_resultat.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)



        self.combo_hsv = QComboBox(self)
        self.combo_hsv.setFont(self.font)
        self.combo_hsv.setStyleSheet("border: 2px solid #5c5c5c; color: white; background-color: rgba(35,35,45,255);")
        self.combo_hsv.addItem("Auto")
        self.combo_hsv.addItem("Manuel-Camera Grand Angle")
        self.combo_hsv.addItem("Manuel-Camera Zoom")
        self.combo_hsv.resize(450,35)
        self.combo_hsv.move(1390,490)
        self.combo_hsv.setCurrentText(self.state_hsv)
        self.combo_hsv.activated[str].connect(self.hsv_change_state)
        
        self.hue_up = 0
        self.hue_low = 0 
        self.hue_up2 = 0
        self.hue_low2 = 0 
        self.sat_up = 0
        self.sat_low = 0 
        self.val_up = 0
        self.val_low = 0 

        self.slider_hue_up = Slider(0, 179, self.hsv_change)
        self.slider_hue_low = Slider(0, 179, self.hsv_change)
        self.slider_hue_up2 = Slider(0, 179, self.hsv_change)
        self.slider_hue_low2 = Slider(0, 179, self.hsv_change)
        self.slider_sat_up = Slider(0, 255, self.hsv_change)
        self.slider_sat_low = Slider(0, 255, self.hsv_change)
        self.slider_val_up = Slider(0, 255, self.hsv_change)
        self.slider_val_low = Slider(0, 255, self.hsv_change)

        self.label_hue_up = Label_Slider('Hue up', self.font3)
        self.label_hue_low = Label_Slider('Hue low', self.font3)
        self.label_hue_up2 = Label_Slider('Hue up2', self.font3)
        self.label_hue_low2 = Label_Slider('Hue low2', self.font3)
        self.label_sat_up = Label_Slider('Sat. up', self.font3)
        self.label_sat_low = Label_Slider('Sat. low', self.font3)
        self.label_val_up = Label_Slider('Val. up', self.font3)
        self.label_val_low = Label_Slider('Val. low', self.font3)

        self.layout_slider = QVBoxLayout(self)
        self.widget_layout = QFrame(self)
        self.widget_layout.move(1390, 550)
        self.widget_layout.resize(450, 400)
        self.widget_layout.setStyleSheet("background-color: rgba(255, 255, 255, 0)")
        self.widget_layout.setLayout(self.layout_slider)
        # self.layout_slider.setGeometry(QtCore.QRect(1435, 460, 400, 550))
        #self.layout_slider.addWidget(self.combo_hsv, 3)
        self.layout_slider.addWidget(self.label_hue_up)
        self.layout_slider.addWidget(self.slider_hue_up)
        self.layout_slider.addWidget(self.label_hue_low)
        self.layout_slider.addWidget(self.slider_hue_low)
        self.layout_slider.addWidget(self.label_hue_up2)
        self.layout_slider.addWidget(self.slider_hue_up2)
        self.layout_slider.addWidget(self.label_hue_low2)
        self.layout_slider.addWidget(self.slider_hue_low2)
        self.layout_slider.addWidget(self.label_sat_up)
        self.layout_slider.addWidget(self.slider_sat_up)
        self.layout_slider.addWidget(self.label_sat_low)
        self.layout_slider.addWidget(self.slider_sat_low)
        self.layout_slider.addWidget(self.label_val_up)
        self.layout_slider.addWidget(self.slider_val_up)
        self.layout_slider.addWidget(self.label_val_low)
        self.layout_slider.addWidget(self.slider_val_low)
        
        # self.widget_layout.show()

        self.checkbox_serial = QCheckBox(self)
        self.checkbox_serial.move(1390, 135)
        self.checkbox_serial.resize(450, 35)
        self.checkbox_serial.setText("Communication avec Arduino")
        self.checkbox_serial.setFont(self.font)
        self.checkbox_serial.setStyleSheet("QCheckBox::indicator{width: 30px; height: 30px; color: white;}QCheckBox{color: white; background-color: rgba(35,35,45,255);}")
        self.checkbox_serial.setChecked(False)
        self.checkbox_serial.toggled.connect(self.CheckboxArduinoComm)
        
        # create the video capture thread
        self.checkbox_ = QCheckBox(self)
        self.checkbox_.move(1390, 255)
        self.checkbox_.resize(450, 35)
        self.checkbox_.setText("CSV")
        self.checkbox_.setFont(self.font)
        self.checkbox_.setStyleSheet("QCheckBox::indicator{width: 30px; height: 30px; color: white;}QCheckBox{color: white; background-color: rgba(35,35,45,255);}")
        self.checkbox_.setChecked(True)
        self.checkbox_.toggled.connect(self.CheckboxCSV)
        


        self.checkbox_recyclage = QCheckBox(self)
        self.checkbox_recyclage.move(1390, 175)
        self.checkbox_recyclage.resize(450, 35)
        self.checkbox_recyclage.setText("Recyclage auto.")
        self.checkbox_recyclage.setFont(self.font)
        self.checkbox_recyclage.setStyleSheet("QCheckBox::indicator{width: 30px; height: 30px; color: white;}QCheckBox{color: white; background-color: rgba(35,35,45,255);}")
        self.checkbox_recyclage.setChecked(False)
        self.checkbox_recyclage.toggled.connect(self.CheckboxAutoRecycle)

        self.checkbox_ignore_recyclage = QCheckBox(self)
        self.checkbox_ignore_recyclage.move(1390, 215)
        self.checkbox_ignore_recyclage.resize(450, 35)
        self.checkbox_ignore_recyclage.setText("Ignorer le recyclage")
        self.checkbox_ignore_recyclage.setFont(self.font)
        self.checkbox_ignore_recyclage.setStyleSheet("QCheckBox::indicator{width: 30px; height: 30px; color: white;}QCheckBox{color: white; background-color: rgba(35,35,45,255);}")
        self.checkbox_ignore_recyclage.setChecked(False)
        self.checkbox_ignore_recyclage.toggled.connect(self.CheckboxIgnoreRecycle)
        # self.thread_test = VideoThread_Zoom()

        self.label_color = QLabel(self)
        self.label_color.move(1650, 315)
        self.label_color.resize(175,120)
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
        self.label_color.setStyleSheet("border: 3px black; border-radius: 15px; background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))

        self.label_data = QLabel(self)

        self.label_data.setStyleSheet("background-color: rgba(255,255,255,0); color: white;")
        self.label_data.setFont(self.font)
        self.label_data.setText('Données des capteurs : \n R = {} \n G = {} \n B = {} \n Lux = {} \n Temp Celsius = {} \n Hum = {} \n'.format(self.color_r, self.color_g, self.color_b, self.color_lux, self.temp, self.hum))
        self.label_data.move(1390, 300)
        self.label_data.adjustSize()
        self.label_data.setAlignment(Qt.AlignLeft)

        self.thread2.change_json_serial_comm.connect(self.update_text)
        # self.thread2.start()


        self.label = QLabel(self)  # Create label
        self.label.setText('SoapVision : Application de vision numérique pour la mini-usine')  # Add text to label
        self.label.setFont(self.font)
        self.label.setStyleSheet("background-color: rgba(255,255,255,0); color: white;")
        self.label.move(10, 980)  
        self.label.resize(850, 40)  
        self.label.setAlignment(Qt.AlignLeft) 

        # Button to start video
        self.ss_video = QPushButton(self)
        self.ss_video.setText('Start video')
        self.ss_video.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.ss_video.setFont(self.font)
        self.ss_video.move(1390, 10)
        self.ss_video.resize(220, 75)
        self.ss_video.clicked.connect(self.ClickStartVideo)
        
        #ComboBox to select soap type
        self.combo_type_savon = QComboBox(self)
        self.combo_type_savon.setFont(self.font)
        self.combo_type_savon.setStyleSheet("border: 2px solid #5c5c5c; color: white; background-color: rgba(35,35,45,255);")
        self.combo_type_savon.addItem('Orange')
        self.combo_type_savon.addItem('Bleu')
        self.combo_type_savon.addItem('Vert')
        self.combo_type_savon.addItem('Autre')
        # self.combo.addItem("Manual - Wide")
        self.combo_type_savon.move(1390, 95)
        self.combo_type_savon.resize(450, 35)
        # self.qlabel = QLabel(self)
        # self.qlabel.move(1500, 61)
        self.combo_type_savon.activated[str].connect(self.onChanged)

        self.btn_test_zoom = QPushButton(self)
        self.btn_test_zoom.setText('Test Cam Zoom')
        self.btn_test_zoom.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.btn_test_zoom.setFont(self.font)
        self.btn_test_zoom.move(1620, 10)
        self.btn_test_zoom.resize(220, 75)
        self.btn_test_zoom.clicked.connect(self.ClickStartTestZoom)

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet("background : lightblue;")  # Setting style sheet to the status bar
        self.setStatusBar(self.status)  # Adding status bar to the main window
        self.status.showMessage('Ready to start')

        self.graph_widget = QFrame(self)
        self.graph_widget.move(10, 590)
        self.graph_widget.resize(760, 385)
        self.graph_widget.setStyleSheet("background-color: black")
        self.plt = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        self.plt.showGrid(x=True, y=True)
        self.plt.addLegend()
        self.plt.setLabel('left', 'Temp/Hum', units='deg C/ %')
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
        self.image_label.move(10, 10)

        self.image_label_zoom = QLabel(self)
        self.disply_width_zoom = 600
        self.display_height_zoom = 450
        self.image_label_zoom.resize(self.disply_width_zoom, self.display_height_zoom)
        self.image_label_zoom.setStyleSheet("background : black;")
        self.image_label_zoom.move(780, 10)

        self.image_label_ia = QLabel(self)
        self.disply_width_ia = 600
        self.display_height_ia = 450
        self.image_label_ia.resize(self.disply_width_zoom, self.display_height_zoom)
        self.image_label_ia.setStyleSheet("background : black;")
        self.image_label_ia.move(780, 530)

        self.timer_hsv = QTimer()
        # self.timer_hsv.setSingleShot(True)
        # self.timer_hsv.timeout.connect(self.wait_for_hsv(self.thread_test, False))
        # self.timer_hsv.start(5500)
########################################################################################################################
#                                                   Buttons                                                            #
########################################################################################################################

    def wait_for_hsv(self, t, wide):
        if self.state_hsv == "Auto":
            t = threading.Timer(1, self.get_first_hsv_val, args=[t, wide])
            t.start()
        # while(self.timer_hsv.isActive()):
        #     if self.timer_hsv.remainingTime() < 300:
        #         self.get_first_hsv_val(t, wide)
        #     else:
        #         timer.sleep(0.1)

    def onChanged(self, text):
        self.combo_hsv.setCurrentText("Auto")
        self.type_savon = text
        if self.thread.isRunning():
            self.thread.type_savon = text
            self.thread.reset_savon_type()
            self.wait_for_hsv(self.thread, True)
        if self.thread_test.isRunning():
            self.thread_test.type_savon = text
            self.thread_test.reset_savon_type()
            self.wait_for_hsv(self.thread_test, False)
        # if self.thread.isRunning():
        #     self.wait_for_hsv()
        # self.qlabel.adjustSize()
    
    def CheckboxArduinoComm(self):
        if self.checkbox_serial.isChecked() == True:
            self.thread2.start()
        else:
            self.thread2.stop()
            self.color_r = 0
            self.color_g = 0
            self.color_b = 0
            self.color_lux = 0
            self.temp = 0
            self.hum = 0
    
    def CheckboxCSV(self):
        if self.checkbox_.isChecked() == True:
            self.csv_enabled = True
        else:
            self.csv_enabled = False

    def CheckboxAutoRecycle(self):
        if self.checkbox_recyclage.isChecked() == True:
            self.thread.toggle_autorecycle(True)
        else:
            self.thread.toggle_autorecycle(False)

    def CheckboxIgnoreRecycle(self):
        if self.checkbox_ignore_recyclage.isChecked() == True:
            self.thread.toggle_ignore_recycle(True)
            self.checkbox_recyclage.setChecked(False)
            self.checkbox_recyclage.setEnabled(False)
        else:
            self.thread.toggle_ignore_recycle(False)
            self.checkbox_recyclage.setEnabled(True)

    def hsv_change_text(self):
        self.label_hue_up.setText('Hue up: {}'.format(self.hue_up))
        self.label_hue_low.setText('Hue low: {}'.format(self.hue_low))
        self.label_hue_low.setText('Hue low: {}'.format(self.hue_low))
        self.label_hue_up2.setText('Hue up2: {}'.format(self.hue_up2))
        self.label_hue_low2.setText('Hue low2: {}'.format(self.hue_low2))
        self.label_sat_up.setText('Sat. up: {}'.format(self.sat_up))
        self.label_sat_low.setText('Sat. low: {}'.format(self.sat_low))
        self.label_val_up.setText('Val. up: {}'.format(self.val_up))
        self.label_val_low.setText('Val. low: {}'.format(self.val_low))

    def hsv_change_value(self):
        self.slider_hue_up.setValue(self.hue_up)
        self.slider_hue_low.setValue(self.hue_low)
        self.slider_hue_up2.setValue(self.hue_up2)
        self.slider_hue_low2.setValue(self.hue_low2)
        self.slider_sat_up.setValue(self.sat_up)
        self.slider_sat_low.setValue(self.sat_low)
        self.slider_val_up.setValue(self.val_up)
        self.slider_val_low.setValue(self.val_low) 

    def hsv_change(self, slider):
        if self.state_hsv != 'Auto':
            self.hue_up = self.slider_hue_up.value()
            self.hue_low = self.slider_hue_low.value()
            self.hue_up2 = self.slider_hue_up2.value()
            self.hue_low2 = self.slider_hue_low2.value()
            self.sat_up = self.slider_sat_up.value()
            self.sat_low = self.slider_sat_low.value()
            self.val_up = self.slider_val_up.value()
            self.val_low = self.slider_val_low.value()
            if self.thread.isRunning():
                self.push_hsv_val(self.thread, self.state_hsv)
            if self.thread_test.isRunning():
                self.push_hsv_val(self.thread_test, self.state_hsv)
            self.hsv_change_text()
   

    def get_first_hsv_val(self, t, wide):
        if self.state_hsv == 'Auto':
            if wide:
                self.hue_up = t.u_b[0]
                self.hue_low = t.l_b[0]
                self.sat_up = t.u_b[1]
                self.sat_low = t.l_b[1]
                self.val_up = t.u_b[2]
                self.val_low = t.l_b[2]
                self.hue_up2 = 0
                self.hue_low2 = 0
                
            else:
                self.hue_up2 = t.u_b2_z[0]
                self.hue_low2 = t.l_b2_z[0]
                
                self.hue_up = t.u_b_z[0]
                self.hue_low = t.l_b_z[0]
                self.sat_up = t.u_b_z[1]
                self.sat_low = t.l_b_z[1]
                self.val_up = t.u_b_z[2]
                self.val_low = t.l_b_z[2]

            self.hsv_change_text()
            self.hsv_change_value()
    
            
       
    def hsv_change_state(self, state): # State pour modifier le HSV
        self.state_hsv = state
            

# "Manuel-Camera Grand Angle"
# "Manuel-Camera Zoom"
        
#self.thread.state = text

    def push_hsv_val(self, thread_, state):
        if state == "Manuel-Camera Grand Angle":
            thread_.l_b = np.array([self.hue_low, self.sat_low , self.val_low])
            thread_.u_b = np.array([self.hue_up,  self.sat_up, self.val_up])
        
        if state == "Manuel-Camera Zoom":
            thread_.l_b_z = np.array([self.hue_low, self.sat_low, self.val_low])
            thread_.u_b_z = np.array([self.hue_up, self.sat_up, self.val_up])
            thread_.l_b2_z = np.array([self.hue_low2, self.sat_low, self.val_low])
            thread_.u_b2_z = np.array([self.hue_up2, self.sat_up, self.val_up])


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
        # self.thread.change_pixmap_signal_zoom_view.connect(self.thread_ai.get_image)
        self.thread.change_pixmap_signal_zoom_view.connect(self.update_image_zoom, Qt.QueuedConnection)
        self.thread.change_pixmap_signal_ai.connect(self.update_image_ai, Qt.QueuedConnection)
        # self.thread_ai.change_pixmap_signal_ai.connect(self.update_image_ai)
        # self.thread.change_pixmap_signal_ai.connect(self.update_image_zoom, Qt.QueuedConnection)
        # start the thread
        self.thread.start()
        self.ss_video.clicked.connect(self.thread.stop)  # Stop the video if button clicked
        self.ss_video.clicked.connect(self.ClickStopVideo)
        self.combo_hsv.setEnabled(True)
        self.wait_for_hsv(self.thread, True)
        # self.thread_ai.set
        
        # self.timer_hsv.timeout.connect(self.wait_for_hsv())
        # self.timer_hsv.start(5500)

    # Activates when Start/Stop video button is clicked to Stop (ss_video)
    def ClickStopVideo(self):
        self.combo_hsv.setEnabled(False)
        self.btn_test_zoom.setEnabled(True)
        self.thread.change_pixmap_signal_wide_view.disconnect()
        self.thread.change_pixmap_signal_zoom_view.disconnect()
        self.thread.change_pixmap_signal_ai.disconnect()
        # self.thread_ai.change_pixmap_signal_ai.disconnect()
        self.ss_video.setText('Start video')
        self.ss_video.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.status.showMessage('Ready to start')
        self.ss_video.clicked.disconnect(self.ClickStopVideo)
        self.ss_video.clicked.disconnect(self.thread.stop)
        self.ss_video.clicked.connect(self.ClickStartVideo)
        # self.timer_hsv.timeout.disconnect(self.wait_for_hsv(self.thread, True))
        
        
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
        self.thread_test.change_pixmap_signal_test_wide_view.connect(self.update_image_zoom, Qt.QueuedConnection)
        # start the thread
        self.thread_test.start()
        self.btn_test_zoom.clicked.connect(self.thread_test.stop)  # Stop the video if button clicked
        self.btn_test_zoom.clicked.connect(self.ClickStopTestZoom)
        # self.timer_hsv.timeout.connect(self.wait_for_hsv(self.thread_test, False))
        # self.timer_hsv.start(5500)
        self.combo_hsv.setEnabled(True)
        self.wait_for_hsv(self.thread_test, False)

    # Activates when Start/Stop video button is clicked to Stop (ss_video)
    def ClickStopTestZoom(self):
        self.combo_hsv.setEnabled(False)
        if self.ss_video.isEnabled() == False:
            self.ss_video.setEnabled(True)
        self.thread_test.change_pixmap_signal_test_zoom_view.disconnect()
        self.thread_test.change_pixmap_signal_test_wide_view.disconnect()
        self.btn_test_zoom.setText('Start Test Zoom')
        self.btn_test_zoom.setStyleSheet("background-color: rgb(102, 255, 153);")
        self.btn_test_zoom.clicked.disconnect(self.ClickStopTestZoom)
        self.btn_test_zoom.clicked.disconnect(self.thread_test.stop)
        self.btn_test_zoom.clicked.connect(self.ClickStartTestZoom)
        # self.timer_hsv.timeout.disconnect(self.wait_for_hsv(self.thread_test, True))
        

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

    
    def update_image_ai(self, result):
        """Updates the image_label with a new opencv image"""
        # qt_img_temp = ImageQt(Image.fromarray((np.argmax(result, axis=0) * 255 / result.shape[0]).astype(np.uint8)))
        # qt_img = QtGui.QPixmap.fromImage(qt_img_temp)
        qt_img = self.convert_cv_qt_zoom(cv_img2)
        self.image_label_ia.setPixmap(qt_img)
        self.image_name = self.thread.img_name
        self.mask_name = self.thread.mask_name
        if self.csv_enabled:    
            data_to_append = []
            data_to_append.append(str(time_string()))
            data_to_append.append(self.image_name)
            data_to_append.append(self.mask_name)
            data_to_append.append(self.temp)
            data_to_append.append(self.hum)
            data_to_append.append(self.color_lux)
            data_to_append.append(self.color_r)
            data_to_append.append(self.color_g)
            data_to_append.append(self.color_b)
            self.CSV._append_to_csv(data_to_append)
    

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
        # rgb_image = cv_img
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
        self.label_color.setStyleSheet("border: 5px black; border-radius: 15px; background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))
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
        if self.thread2.isRunning == True:
            self.thread2.stop()
        if (self.thread.isRunning() == True) or (self.thread_test.isRunning() == True):
            event.ignore()
        else:
            event.accept()

logging.basicConfig(format="%(message)s", level=logging.INFO)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec())
