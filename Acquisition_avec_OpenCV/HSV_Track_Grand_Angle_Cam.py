import cv2
import numpy as np
import os
from csi_camera import CSI_Camera
from tracker import *
from OPC_UA import *
import time
import asyncio

path = '/home/jetson_user/Projet/Code/Nano/Camera/Dernier_Code/Acquisition_avec_OpenCV/Images_15oct2021'

show_fps = True
tracker = EuclideanDistTracker()

OPCUA = OPCUACommunication()



def nothing(x):
    pass
# Simple draw label on an image; in our case, the video frame
def draw_label(cv_image, label_text, label_position):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    color = (255,255,255)
    # You can get the size of the string with cv2.getTextSize here
    cv2.putText(cv_image, label_text, label_position, font_face, scale, color, 1, cv2.LINE_AA)

def read_camera(csi_camera,display_fps):
    _ , camera_image=csi_camera.read()
    if display_fps:
        draw_label(camera_image, "Frames Displayed (PS): "+str(csi_camera.last_frames_displayed),(10,20))
        draw_label(camera_image, "Frames Read (PS): "+str(csi_camera.last_frames_read),(10,40))
    return camera_image

DISPLAY_WIDTH=960
DISPLAY_HEIGHT=720

SENSOR_MODE_720=3

def start_cameras():
    
    cv2.namedWindow('Trackbars')
    cv2.createTrackbar('hueLower', 'Trackbars',91,179,nothing)
    cv2.createTrackbar('hueUpper', 'Trackbars',106,179,nothing)
    cv2.createTrackbar('satLow', 'Trackbars',91,255,nothing)
    cv2.createTrackbar('satHigh', 'Trackbars',255,255,nothing)
    cv2.createTrackbar('valLow','Trackbars',126,255,nothing)
    cv2.createTrackbar('valHigh','Trackbars',255,255,nothing)

    left_camera = CSI_Camera()
    left_camera.create_gstreamer_pipeline(
            sensor_id=0,
            sensor_mode=3,
            framerate=30,
            flip_method=0,
            display_height=DISPLAY_HEIGHT,
            display_width=DISPLAY_WIDTH,
    )
    left_camera.open(left_camera.gstreamer_pipeline)
    left_camera.start()

    right_camera = CSI_Camera()
    right_camera.create_gstreamer_pipeline(
            sensor_id=1,
            sensor_mode=3,
            framerate=30,
            flip_method=0,
            display_height=DISPLAY_HEIGHT,
            display_width=DISPLAY_WIDTH,
    )
    right_camera.open(right_camera.gstreamer_pipeline)
    right_camera.start()

    cv2.namedWindow("CSI Cameras", cv2.WINDOW_NORMAL)
    cv2.namedWindow("HSV-Mask and Track", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Object Track", cv2.WINDOW_NORMAL)
    if (
        #not right_camera.video_capture.isOpened()
    ):
        # Cameras did not open, or no camera attached

        print("Unable to open any cameras")
        # TODO: Proper Cleanup
        SystemExit(0)
    try:
        right_camera.start_counting_fps()
        left_camera.start_counting_fps()
        while cv2.getWindowProperty("CSI Cameras", 0) >= 0 :
            #left_image = read_camera(left_camera, False)
            img=cv2.VideoCapture(0)
            hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

            hueLow=cv2.getTrackbarPos('hueLower', 'Trackbars')
            hueUp=cv2.getTrackbarPos('hueUpper', 'Trackbars')
            
            Ls=cv2.getTrackbarPos('satLow', 'Trackbars')
            Us=cv2.getTrackbarPos('satHigh', 'Trackbars')
        
            Lv=cv2.getTrackbarPos('valLow', 'Trackbars')
            Uv=cv2.getTrackbarPos('valHigh', 'Trackbars')
        
            l_b=np.array([hueLow,Ls,Lv])
            u_b=np.array([hueUp,Us,Uv])
                
            FGmask=cv2.inRange(hsv,l_b,u_b)
            FG_Obj = cv2.bitwise_and(img, img, mask=FGmask)
            right_camera.frames_displayed += 1 
            contours, _ = cv2.findContours(FGmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detections = []
            for cnt in contours:
                # Calculate area and remove small elements
                area = cv2.contourArea(cnt)
                if area > 5000 :
                    cv2.drawContours(img, [cnt], -1, (0, 0, 255), 1)
                    x, y, w, h = cv2.boundingRect(cnt)
                    # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    detections.append([x, y, w, h])

            boxes_ids = tracker.update(detections)
            for box_id in boxes_ids:
                x, y, w, h, id = box_id
                cv2.putText(img, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if 420 <= x and x+w <=650 and 275 <= y and y+h<= 425:
                    loop = asyncio.run(OPCUA.pause_convoyeur_coupe())
                    # coroutine = OPCUA.pause_convoyeur_coupe()
                    # loop.run_until_complete(coroutine)
                    time.sleep(0.1)
                    left_image = read_camera(left_camera, False)
                    cv2.imwrite(os.path.join(path , 'test%d_x%d_y%d.jpg') % (id,x,y), left_image)  
            cv2.rectangle(img, (420, 275), (650, 425), (0, 0, 255), 1)
            cv2.imshow("CSI Cameras", img)
            cv2.imshow("HSV-Mask and Track",FGmask) #  FGmaskComp
            cv2.imshow("Object Track", FG_Obj)
            if (cv2.waitKey(20) & 0xFF) == 27:
                break   

    finally:
        right_camera.stop()
        right_camera.release()
        left_camera.stop()
        left_camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_cameras()