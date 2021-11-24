import cv2
import numpy as np
import os
from csi_camera import CSI_Camera
from tracker import *
from OPC_UA import *
import time
import asyncio

cap = cv2.VideoCapture(0)
if(cap.isOpened()):
    print(cap.isOpened())


            # "nvarguscamerasrc sensor-id=0 sensor-mode=3 ! video/x-raw(memory:NVMM), format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv flip-method=0 ! video/x-raw, width=(int)1280, height=(int)720, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"