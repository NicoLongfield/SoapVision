import serial
from PyQt5 import QtCore, QtWidgets
import time
import json
import threading
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QComboBox, QLabel, QPushButton, QVBoxLayout, QMainWindow, QDesktopWidget, QStatusBar
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
#arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
#class ArduinoSensors():

#   def __init__(self):
# #      print("Arduino init...")
# arduino = serial.Serial(
#     port = '/dev/ttyACM0',
#     baudrate = 115200,
#     bytesize = serial.EIGHTBITS,
#     parity = serial.PARITY_NONE,
#     stopbits = serial.STOPBITS_ONE,
#     timeout = 5,
#     xonxoff = False,
#     rtscts = False,
#     dsrdtr = False,
#     writeTimeout = 2
# )
# arduino.reset_input_buffer()
# #       self.running = False


# def update_serial():
#     while True:
#         data = arduino.readline().decode("utf-8")
#         try:
#             dict_json = json.loads(data)
#             print(dict_json)
#         except json.JSONDecodeError as e:
#             dict_json = {}


# #
# #def stop_serial(self):
# #    self.running = False
# #    self.read_thread.join()


# def print_to_inf(dict_args):
#     while True:
#         print(dict_args)
#         time.sleep(5)

# # loop = asyncio.get_event_loop()
# if __name__ == "__main__":
#  #   arduino_serial = threading.Thread(target=update_serial(), kwar)
#     update_serial()



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
    def __init__(self):
        super(MyWindow, self).__init__()
        # self.available_cameras = QCameraInfo.availableCameras()  # Getting available cameras

        cent = QDesktopWidget().availableGeometry().center()  # Finds the center of the screen
        self.setStyleSheet("background-color: rgb(30, 59, 75);")
        self.resize(300, 300)
        self.frameGeometry().moveCenter(cent)
        self.setWindowTitle('S O A P V I S I O N')
        self.initWindow()

########################################################################################################################
#                                                   Windows                                                            #
########################################################################################################################
    def initWindow(self):
        # create the video capture thread
        self.thread = Arduiuno_Comm()

        # Label with the name of the co-founders
        self.label = QLabel(self)  # Create label
        self.label.setText('SoapVision : Application de vision num/rique pour la mini-usine')  # Add text to label
        self.label.move(30, 30)  # Allocate label in window
        self.label.resize(10, 50)  # Set size for the label
        self.label.adjustSize()
        self.label.setAlignment(Qt.AlignLeft)  # Align text in the label

        self.label_color = QLabel(self)
        self.label_color.move(30, 60)
        self.label_color.resize(40,40)
        self.label_color.setAutoFillBackground(True)
        self.color_r = 0
        self.color_g = 0
        self.color_b = 0
        self.label_color.setStyleSheet("background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))
        #values = "{r} {g} {b} {a}".format(r = color.red)


        self.thread.change_json_serial_comm.connect(self.update_text)
        self.thread.start()
        # #ComboBox to select soap type
        # self.combo = QComboBox(self)
        # self.combo.addItem("Orange")
        # self.combo.addItem("Bleu")
        # self.combo.addItem("Vert")
        # self.combo.move(1500, 95)
        # # self.qlabel = QLabel(self)
        # # self.qlabel.move(1500, 61)
        # self.combo.activated[str].connect(self.onChanged)

        # # Status bar
        # self.status = QStatusBar()
        # self.status.setStyleSheet("background : lightblue;")  # Setting style sheet to the status bar
        # self.setStatusBar(self.status)  # Adding status bar to the main window
        # self.status.showMessage('Ready to start')

    def update_text(self, str_json):
        self.label.setText(json.dumps(str_json))
        if "R" in str_json:
            self.color_r = str_json["R"]
            self.color_g = str_json["G"]
            self.color_b = str_json["B"]
        self.label_color.setStyleSheet("background-color: rgb({}, {}, {});".format(self.color_r, self.color_g, self.color_b))
        self.label.adjustSize()

    def closeEvent(self, event):
        if self.thread._run_flag == True:
            self.thread.stop()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec())