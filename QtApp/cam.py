from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from csi_camera import CSI_Camera
from tracker import *
from OPC_UA import *
from Time_func import *
from pathlib import Path
time_init()


path = '/home/jetson_user/Projet/Images/' + time.strftime('%d_%b_%Y')
Path(path).mkdir(parents=True, exist_ok=True)



    


    # return upper_bound, lower_bound




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

show_fps = True

tracker = EuclideanDistTracker()
OPCUA = OPCUACommunication()
OPCUA_Pause = sys.argv[1]

SENSOR_MODE_720 = 3
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 720

class VideoThread(QThread):
    # change_pixmap_signal = pyqtSignal(np.ndarray)
    
    change_pixmap_signal_wide_view = pyqtSignal(np.ndarray)
    change_pixmap_signal_zoom_view = pyqtSignal(np.ndarray)
    left_camera = CSI_Camera()
    right_camera = CSI_Camera()
    def __init__(self):
        super().__init__()
        self.control_state = ''
        self.OPCUA = OPCUA_Pause
        self.target_to_recycle = -1
        self.ignore_recycle = False
        self.recycle = False
        self.autorecycle = False
        self._run_flag = False
        self.stopped = True
        self.type_savon = 'Orange'
        self.u_b, self.l_b, = self.savon_type_wide()
        self.u_b_z, self.l_b_z, self.u_b2_z, self.l_b2_z = self.savon_type_zoom()
    def run(self):
        self._run_flag = True
        self.stopped = False
        self.left_camera.create_gstreamer_pipeline(
        sensor_id=0,
        sensor_mode=SENSOR_MODE_720,
        framerate=30,
        flip_method=0,
        display_height=DISPLAY_HEIGHT,
        display_width=DISPLAY_WIDTH,
        )
        self.left_camera.open(self.left_camera.gstreamer_pipeline)
        self.left_camera.start()
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
                    not self.right_camera.video_capture.isOpened() or not self.left_camera.video_capture.isOpened()
            ):
            print("Unable to open any cameras")
            SystemExit(0)
        
        delayv = 0.5
        last = -1
        new = False
        target_to_recycle = -1
        try:
            
            #self.left_camera.start_counting_fps()
            self.right_camera.start_counting_fps()
            while self._run_flag:
                img = read_camera(self.right_camera, show_fps)
                mask_roi = np.zeros(img.shape[:2], dtype="uint8")
                cv2.rectangle(mask_roi, (100,275), (850, 465), 255, -1)
                hsv = cv2.bitwise_and(img, img, mask=mask_roi)
                hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
                
                # up_bound, low_bound = savon_type_wide(self.type_savon)
                

                FGmask = cv2.inRange(hsv, self.l_b, self.u_b)
                
                contours, _ = cv2.findContours(FGmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                detections = []
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 5000:
                        cv2.drawContours(img, [cnt], -1, (0, 0, 255), 1)
                        x, y, w, h = cv2.boundingRect(cnt)
                        detections.append([x, y, w, h])

                boxes_ids = tracker.update(detections)
                
                for box_id in boxes_ids:
                    x, y, w, h, id = box_id
                    cv2.putText(img, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    if 440 <= x and x + w <= 680 and id != last:
                        # self.u_b, self.l_b, self.u_b2, self.l_b2 = savon_type_zoom(self.type_savon)
                        last = id
                        img_name = 'Ocean_' + str(id) + '_' + str(time_string()) + '.jpg'  #####
                        if self.OPCUA:
                            asyncio.run(OPCUA.pause_convoyeur_coupe())
                        print("PAUSE!!!")
                        asyncio.run(self.write_zoom_img(path, img_name, delayv, self.left_camera, last)) #####concurrent.futures.ThreadPoolExecutor.submit
                        
                    if not self.ignore_recycle:
                        if (id == self.target_to_recycle or self.autorecycle) and 685 <= x and x+w <= 850:
                            asyncio.run(OPCUA.appel_recyclage(0.15, 0.9))

                cv2.rectangle(img, (460, 300), (680, 440), (0, 255, 0), 2)
                cv2.rectangle(img, (675, 300), (850, 440), (0, 0, 255), 2)
                cv_img = img
                self.right_camera.frames_displayed+=1
                self.change_pixmap_signal_wide_view.emit(cv_img)
                self.msleep(25)
        finally:
            
            self.right_camera.stop()
            self.right_camera.release()
            self.left_camera.stop()
            self.left_camera.release_left()
            self.stopped = True



    async def write_zoom_img(self, path_, img_name_, delay, csi_camera, last):
        await asyncio.sleep(delay)
        l_b, u_b, l_b2, u_b2 = self.l_b_z, self.u_b_z, self.l_b2_z, self.u_b2_z
        # time.sleep(delay)
        _, img_being_written = csi_camera.read()
        img_being_written = img_being_written[200:650,:]
        hsv = cv2.cvtColor(img_being_written, cv2.COLOR_BGR2HSV)
        # u_b, l_b, u_b2, l_b2 = savon_type_zoom(self.type_savon)
        FGmask1_zoom = cv2.inRange(hsv, l_b, u_b)
        FGmask2_zoom = cv2.inRange(hsv, l_b2, u_b2)
        # FGmask_blanc = cv2.inRange(img_being_written,np.array([220,220,220]), np.array([255,255,255]))
        FGmask_zoom = cv2.add(FGmask1_zoom, FGmask2_zoom)#, FGmask_blanc)
        # FG_Obj_zoom = cv2.bitwise_and(img_being_written, img_being_written, mask=FGmask_zoom)
        contours, _ = cv2.findContours(FGmask_zoom, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(contours, key=cv2.contourArea)

        box = cv2.boxPoints(cv2.minAreaRect(c))
        x, y, w, h = cv2.boundingRect(box)

        x = np.int32((x+math.floor(w/2))-175)
        y = np.int32((y+math.floor(h/2))-150)
        w = np.int32(350)
        h = np.int32(300)
        
        mask = np.full((img_being_written.shape[0], img_being_written.shape[1]), 0, dtype=np.uint8)
        cv2.drawContours(mask, [c], 0, (255,255,255), -1)
        cv2.drawContours(mask, [c], 0, (255,255,255), 3)
        out = cv2.bitwise_and(img_being_written, img_being_written, mask=mask)
        roi = out[y:y+h,x:x+w]
        # self.change_pixmap_signal_zoom_view.emit(img_being_written)
        if roi.size != 0:
            self.target_to_recycle = last
            self.change_pixmap_signal_zoom_view.emit(roi)
            cv2.imwrite(os.path.join(path_, img_name_), out)
            
        # return img_being_written
    def toggle_autorecycle(self, state):
        self.autorecycle = state

    def toggle_ignore_recycle(self, state):
        self.ignore_recycle = state

    def savon_type_wide(self):

        lower_bound = np.array([0, 50, 126])
        upper_bound = np.array([30, 255, 255])
        if self.type_savon == 'Orange':
            lower_bound = np.array([0, 50, 126])
            upper_bound = np.array([30, 255, 255])

        if self.type_savon == 'Bleu':
            lower_bound = np.array([93, 88, 134])
            upper_bound = np.array([103, 255, 255])

        if self.type_savon == 'Vert':
            lower_bound = np.array([46, 38, 160])
            upper_bound = np.array([70, 255, 255])

        else:
            lower_bound = np.array([0, 50, 126])
            upper_bound = np.array([30, 255, 255])

        return upper_bound, lower_bound

    def savon_type_zoom(self):
        lower_bound = np.array([0, 15, 65])
        upper_bound = np.array([45, 255, 220])
        lower_bound2 = np.array([140, 13, 65])
        upper_bound2 = np.array([179, 255, 220])
        if self.type_savon == 'Orange':
            lower_bound = np.array([0, 15, 65])
            upper_bound = np.array([45, 255, 220])
            lower_bound2 = np.array([140, 13, 65])
            upper_bound2 = np.array([179, 255, 220])

        if self.type_savon == 'Vert':
            lower_bound = np.array([0, 0, 125])
            upper_bound = np.array([63, 84, 255])
            lower_bound2 = np.array([157, 0, 125])
            upper_bound2 = np.array([179, 84, 255])
        
        if self.type_savon == 'Bleu':
            lower_bound = np.array([80, 10, 120])
            upper_bound = np.array([122, 179, 175])        
            lower_bound2 = np.array([179, 10, 120])
            upper_bound2 = np.array([179, 179, 175])
        else:
            lower_bound = np.array([0, 15, 65])
            upper_bound = np.array([45, 255, 220])
            lower_bound2 = np.array([140, 13, 65])
            upper_bound2 = np.array([179, 255, 220])
        return upper_bound, lower_bound, upper_bound2, lower_bound2

        
    # def getSlider_val(self, ub, lb):
    #     self.up_bound, self.low_bound = ub, lb

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        # self.join()


class VideoThread_Zoom(QThread):
    change_pixmap_signal_test_zoom_view = pyqtSignal(np.ndarray)
    change_pixmap_signal_test_wide_view = pyqtSignal(np.ndarray)
    left_camera = CSI_Camera()
    right_camera = CSI_Camera()
    
    
    def __init__(self):
        super().__init__()
        self._run_flag = False
        self.stopped = True
        self.type_savon = 'Orange'
        self.u_b, self.l_b, = self.savon_type_wide()
        # self.u_b_z, self.l_b_z, self.u_b2_z, self.l_b2_z = self.savon_type_zoom()
        self.u_b_z, self.l_b_z, self.u_b2_z, self.l_b2_z = self.savon_type_zoom()

    def run(self):
        self._run_flag = True
        self.stopped = False
        self.left_camera.create_gstreamer_pipeline(
            sensor_id=0,
            sensor_mode=SENSOR_MODE_720,
            framerate=30,
            flip_method=0,
            display_height=DISPLAY_HEIGHT,
            display_width=DISPLAY_WIDTH,
        )
        self.left_camera.open(self.left_camera.gstreamer_pipeline)
        self.left_camera.start()

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
                    not self.right_camera.video_capture.isOpened() or not self.left_camera.video_capture.isOpened()
            ):
            print("Unable to open any cameras")
            SystemExit(0)
        delayv = 0.5
        last = -1
        new = False
        
        try:
            self.right_camera.start_counting_fps()
            while self._run_flag:
                img_right = read_camera(self.right_camera, True)
                img = read_camera(self.left_camera, False)
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                hsv_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2HSV)
                # self.u_b, self.l_b, self.u_b2, self.l_b2 = savon_type_zoom(self.type_savon)
                FGmask = cv2.inRange(hsv_right, self.l_b, self.u_b)
                FGmask1_zoom = cv2.inRange(hsv, self.l_b_z, self.u_b_z)
                FGmask2_zoom = cv2.inRange(hsv, self.l_b2_z, self.u_b2_z)
                FGmask_zoom = cv2.add(FGmask1_zoom, FGmask2_zoom)
                contours_zoom, _ = cv2.findContours(FGmask_zoom, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours, _ = cv2.findContours(FGmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours_zoom:
                    # Calculate area and remove small elements
                    area = cv2.contourArea(cnt)
                    if area > 5000:
                        cv2.drawContours(img, [cnt], -1, (0, 0, 255), 1)
                        x, y, w, h = cv2.boundingRect(cnt)
                        if y >= 100 and y + h <= 600:
                            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                
                detections = []
                for cnt in contours:
                    # Calculate area and remove small elements
                    area = cv2.contourArea(cnt)
                    if area > 5000:
                        cv2.drawContours(img_right, [cnt], -1, (0, 0, 255), 1)
                        x, y, w, h = cv2.boundingRect(cnt)
                        if y >= 275 and y + h <= 465:
                            detections.append([x, y, w, h])

                boxes_ids = tracker.update(detections)
                
                for box_id in boxes_ids:
                    x, y, w, h, id = box_id
                    cv2.putText(img_right, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                    cv2.rectangle(img_right, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv_img = img
                cv_img2 = img_right
                cv2.rectangle(img, (460, 200), (680, 650), (0, 0, 255), 2)
                self.change_pixmap_signal_test_zoom_view.emit(cv_img)
                self.change_pixmap_signal_test_wide_view.emit(cv_img2)
                self.right_camera.frames_displayed+=1
                self.msleep(10)
        finally:
            self.right_camera.stop()
            self.right_camera.release()
            self.left_camera.stop()
            self.left_camera.release_left()
            self.stopped = True

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        # self.join()
    
    def savon_type_wide(self):

        lower_bound = np.array([0, 50, 126])
        upper_bound = np.array([30, 255, 255])
        if self.type_savon == 'Orange':
            lower_bound = np.array([0, 50, 126])
            upper_bound = np.array([30, 255, 255])

        if self.type_savon == 'Bleu':
            lower_bound = np.array([93, 88, 134])
            upper_bound = np.array([103, 255, 255])

        if self.type_savon == 'Vert':
            lower_bound = np.array([46, 38, 160])
            upper_bound = np.array([70, 255, 255])

        else:
            lower_bound = np.array([0, 50, 126])
            upper_bound = np.array([30, 255, 255])

        return upper_bound, lower_bound

    def savon_type_zoom(self):
        lower_bound = np.array([0, 15, 65])
        upper_bound = np.array([45, 255, 220])
        lower_bound2 = np.array([140, 13, 65])
        upper_bound2 = np.array([179, 255, 220])
        if self.type_savon == 'Orange':
            lower_bound = np.array([0, 15, 65])
            upper_bound = np.array([45, 255, 220])
            lower_bound2 = np.array([140, 13, 65])
            upper_bound2 = np.array([179, 255, 220])

        if self.type_savon == 'Vert':
            lower_bound = np.array([0, 0, 125])
            upper_bound = np.array([63, 84, 255])
            lower_bound2 = np.array([157, 0, 125])
            upper_bound2 = np.array([179, 84, 255])
        
        if self.type_savon == 'Bleu':
            lower_bound = np.array([80, 10, 120])
            upper_bound = np.array([122, 179, 175])        
            lower_bound2 = np.array([179, 10, 120])
            upper_bound2 = np.array([179, 179, 175])

        else:
            lower_bound = np.array([0, 15, 65])
            upper_bound = np.array([45, 255, 220])
            lower_bound2 = np.array([140, 13, 65])
            upper_bound2 = np.array([179, 255, 220])
        return upper_bound, lower_bound, upper_bound2, lower_bound2

    def setSlider_val(self, up1, low1, up2,low2):
        return up1, low1, up2,low2
        
