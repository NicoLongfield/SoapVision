from csi_camera import CSI_Camera
from tracker import *
import cv2


def nothing(x):
    pass

def draw_label(cv_image, label_text, label_position):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    color = (255,255,255)
    cv2.putText(cv_image, label_text, label_position, font_face, scale, color, 1, cv2.LINE_AA)

def read_camera(csi_camera,display_fps):
    _ , camera_image=csi_camera.read()
    if display_fps:
        draw_label(camera_image, "Frames Displayed (PS): "+str(csi_camera.last_frames_displayed),(10,20))
        draw_label(camera_image, "Frames Read (PS): "+str(csi_camera.last_frames_read),(10,40))
    return camera_image


def init_display():
    cv2.namedWindow('Trackbars')
    cv2.createTrackbar('hueLower', 'Trackbars',91,179,nothing)
    cv2.createTrackbar('hueUpper', 'Trackbars',106,179,nothing)
    cv2.createTrackbar('satLow', 'Trackbars',91,255,nothing)
    cv2.createTrackbar('satHigh', 'Trackbars',255,255,nothing)
    cv2.createTrackbar('valLow','Trackbars',126,255,nothing)
    cv2.createTrackbar('valHigh','Trackbars',255,255,nothing)
    
    cv2.namedWindow("CSI Cameras", cv2.WINDOW_NORMAL)
    cv2.namedWindow("HSV-Mask and Track", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Object Track", cv2.WINDOW_NORMAL)

