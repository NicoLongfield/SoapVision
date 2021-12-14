from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from csi_camera import CSI_Camera
from main import *

def nothing(x):
    pass

SENSOR_MODE_720 = 3
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 720

show_fps = True



# Simple draw label on an image; in our case, the video frame
def draw_label(cv_image, label_text, label_position):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    color = (255, 255, 255)
    # You can get the size of the string with cv2.getTextSize here
    cv2.putText(cv_image, label_text, label_position, font_face, scale, color, 1, cv2.LINE_AA)
    
def read_camera(csi_camera, display_fps):
    _, camera_image = csi_camera.read()

    if display_fps:
        draw_label(camera_image, "Frames Displayed (PS): " + str(csi_camera.last_frames_displayed), (10, 20))
        draw_label(camera_image, "Frames Read (PS): " + str(csi_camera.last_frames_read), (10, 40))
    return camera_image


class VideoThread(QThread):
    change_pixmap_signal_wide_view = pyqtSignal(np.ndarray)
    #left_camera = CSI_Camera()
    right_camera = CSI_Camera()
    def __init__(self):
        super().__init__()

    def run(self):
        #self.left_camera.create_gstreamer_pipeline(
        #sensor_id=0,
        #sensor_mode=SENSOR_MODE_720,
        #framerate=30,
        #flip_method=0,
        #display_height=DISPLAY_HEIGHT,
        #display_width=DISPLAY_WIDTH,
        #)
        #self.left_camera.open(self.left_camera.gstreamer_pipeline)
        #self.left_camera.start()
        self.right_camera.create_gstreamer_pipeline(
        sensor_id=1,
        sensor_mode=SENSOR_MODE_720,
        framerate=30,
        flip_method=0,
        display_height=DISPLAY_HEIGHT,
        display_width=DISPLAY_WIDTH,
        )
        self.right_camera.open(self.right_camera.gstreamer_pipeline)
        self.right_camera.start()
        if (
                    not self.right_camera.video_capture.isOpened()# or not self.right_camera.video_capture.isOpened()
            ):
            print("Unable to open any cameras")
            SystemExit(0)
        try:
            #self.left_camera.start_counting_fps()
            self.right_camera.start_counting_fps()
            while self.right_camera.running:
                self.image = read_camera(self.right_camera, False)
                #left_img = read_camera(self.left_camera, show_fps)
                #self.left_camera.frames_displayed+=1
                self.right_camera.frames_displayed+=1
                if True:
                    self.image = convert_cv_qt(cv_img)#self.change_pixmap_signal_wide_view.emit(cv_img)
                    #self.change_pixmap_signal_zoom_view.emit(left_img)
                    self.msleep(30)
        finally:
            
            self.right_camera.stop()
            self.right_camera.release()
            #self.left_camera.stop()
            #self.left_camera.release()


    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        #self.left_camera.running = False
        self.right_camera.running = False
        self.wait()

    def get_img(self):
        return img

    # def __init__(self):
    #     super().__init__()
    #     self.display_width = 960
    #     self.display_height = 720
    #     # create the label that holds the image
    #     self.image_label = QLabel(self)
    #     self.image_label.resize(self.display_width, self.display_height)
    #     # create a text label
    #     self.textLabel = QLabel('Webcam')
    #
    #     # create a vertical box layout and add the two labels
    #     vbox = QVBoxLayout()
    #     vbox.addWidget(self.image_label)
    #     vbox.addWidget(self.textLabel)
    #     # set the vbox layout as the widgets layout
    #     self.setLayout(vbox)
    #
    #     # create the video capture thread
    #     self.thread = VideoThread()
    #     # connect its signal to the update_image slot
    #     self.thread.change_pixmap_signal.connect(self.update_image)
    #     # start the thread
    #     self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

@pyqtSlot(np.ndarray)
def update_image(QLabel, cv_img):
    """Updates the image_label with a new opencv image"""
    qt_img = convert_cv_qt(cv_img, QLabel)
    QLabel.setPixmap(qt_img)

def convert_cv_qt(cv_img):
    """Convert from an opencv image to QPixmap"""
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
    p = convert_to_Qt_format.scaled(960, 720, Qt.KeepAspectRatio)
    return QPixmap.fromImage(p)

# if __name__=="__main__":
#     app = QApplication(sys.argv)
#     a = App()
#     a.show()
#     sys.exit(app.exec_())
