import time
import cv2
import numpy as np
import os
import sys
import json
from csi_camera import CSI_Camera
from function_cam import *
from tracker import *
from OPC_UA import *
from Time_func import *
from arduino_func import *
from pathlib import Path
import asyncio
import concurrent.futures
import threading
import multiprocessing



show_fps = True

tracker = EuclideanDistTracker()
OPCUA = OPCUACommunication()
OPCUA_Pause = sys.argv[1]
time_init()
print(OPCUA_Pause)

SENSOR_MODE_720 = 3
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 720

path = '/home/jetson_user/Projet/Images/' + time.strftime('%d_%b_%Y')
Path(path).mkdir(parents=True, exist_ok=True)


def write_zoom_img(path_, img_name_, delay):
    time.sleep(delay)
    img_being_written = read_camera(left_camera, False)
    cv2.imwrite(os.path.join(path_, img_name_), img_being_written)


def _append_to_csv(path_folder, csv_filename, csv_headers, data_to_append):
    path__ = path_folder + csv_filename
    no_headers = not os.path.exists(path__) or os.stat(path__).st_size == 0
    with open(csv_filename, 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        if no_headers:
            writer.writerow(csv_headers)
        writer.writerow(data_to_append)


def nothing(x):
    pass


# Simple draw label on an image; in our case, the video frame
def draw_label(cv_image, label_text, label_position):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    color = (255, 255, 255)
    # You can get the size of the string with cv2.getTextSize here
    cv2.putText(cv_image, label_text, label_position, font_face, scale, color, 1, cv2.LINE_AA)


# Read a frame from the camera, and draw the FPS on the image if desired
# Return an image
def read_camera(csi_camera, display_fps):
    _, camera_image = csi_camera.read()

    if display_fps:
        draw_label(camera_image, "Frames Displayed (PS): " + str(csi_camera.last_frames_displayed), (10, 20))
        draw_label(camera_image, "Frames Read (PS): " + str(csi_camera.last_frames_read), (10, 40))
    return camera_image


def start_cameras():
    left_camera = CSI_Camera()
    left_camera.create_gstreamer_pipeline(
        sensor_id=0,
        sensor_mode=SENSOR_MODE_720,
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
        sensor_mode=SENSOR_MODE_720,
        framerate=30,
        flip_method=0,
        display_height=DISPLAY_HEIGHT,
        display_width=DISPLAY_WIDTH,
    )
    right_camera.open(right_camera.gstreamer_pipeline)
    right_camera.start()

    if (
            not left_camera.video_capture.isOpened()
            or not right_camera.video_capture.isOpened()
    ):
        # Cameras did not open, or no camera attached

        print("Unable to open any cameras")
        # TODO: Proper Cleanup
        SystemExit(0)
    try:
        last = -1
        cv2.namedWindow("CSI Cameras", cv2.WINDOW_AUTOSIZE)
        cv2.namedWindow("Trackbars", cv2.WINDOW_AUTOSIZE)
        cv2.createTrackbar('hueLower', 'Trackbars', 91, 179, nothing)
        cv2.createTrackbar('hueUpper', 'Trackbars', 106, 179, nothing)
        cv2.createTrackbar('satLow', 'Trackbars', 91, 255, nothing)
        cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
        cv2.createTrackbar('valLow', 'Trackbars', 126, 255, nothing)
        cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

        # cv2.namedWindow("HSV-Mask and Track", cv2.WINDOW_AUTOSIZE)
        # cv2.namedWindow("Object Track", cv2.WINDOW_NORMAL)
        right_camera.start_counting_fps()
        # left_camera.start_counting_fps()
        ard_p = multiprocessing.Process(target=update_serial)
        ard_p.start()
        while cv2.getWindowProperty("CSI Cameras", 0) >= 0:

            img = read_camera(right_camera, show_fps)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
            hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')

            Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
            Us = cv2.getTrackbarPos('satHigh', 'Trackbars')

            Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
            Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

            l_b = np.array([hueLow, Ls, Lv])
            u_b = np.array([hueUp, Us, Uv])

            FGmask = cv2.inRange(hsv, l_b, u_b)
            # FG_Obj = cv2.bitwise_and(img, img, mask=FGmask)
            right_camera.frames_displayed += 1
            contours, _ = cv2.findContours(FGmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detections = []
            print(dict_json.get("dht_temp"))
            for cnt in contours:
                # Calculate area and remove small elements
                area = cv2.contourArea(cnt)
                if area > 5000:
                    cv2.drawContours(img, [cnt], -1, (0, 0, 255), 1)
                    x, y, w, h = cv2.boundingRect(cnt)
                    if y >= 275 and y + h <= 465:
                        detections.append([x, y, w, h])

            boxes_ids = tracker.update(detections)
            for box_id in boxes_ids:
                x, y, w, h, id = box_id
                cv2.putText(img, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if 440 <= x and x + w <= 680 and id != last:
                    if OPCUA_Pause:
                        asyncio.run(OPCUA.pause_convoyeur_coupe())
                        print("PAUSE!!!")
                    # coroutine = OPCUA.pause_convoyeur_coupe()
                    # loop.run_until_complete(coroutine)
                    # time.sleep(0.39)
                    last = id
                    img_name = 'Ocean_' + str(id) + '_' + str(time_string()) + '.jpg'  #####
                    concurrent.futures.ThreadPoolExecutor.submit(write_zoom_img, (path, img_name, 0.39))  #####

                    # cv2.imwrite(os.path.join(path , 'Ocean_%d_'+ str(time_string()) +'.jpg') % (id), read_camera(left_camera, False))
            cv2.rectangle(img, (460, 300), (680, 440), (0, 0, 255), 1)
            cv2.imshow("CSI Cameras", img)
            cv2.imshow("HSV-Mask and Track", FGmask)  # FGmaskComp
            # cv2.imshow("Object Track", FG_Obj)

            if (cv2.waitKey(10) & 0xFF) == 27:
                break

    finally:
        right_camera.stop()
        right_camera.release()
        left_camera.stop()
        left_camera.release_left()
    cv2.destroyAllWindows()
    ard_p.join(timeout=5)


if __name__ == "__main__":
    start_cameras()
