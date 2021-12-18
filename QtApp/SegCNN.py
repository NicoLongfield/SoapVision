import os
import time
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
import logging
from utils.data_loading import BasicDataset
from unet import UNet
from utils.utils import plot_img_and_mask

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer


class SegNet(QThread):
    change_pixmap_signal_ai = pyqtSignal(np.ndarray)
    def __init__(self):
        super().__init__()
        self.net = UNet(n_channels=1, n_classes=2)
        self.model = './checkpoint_epoch20.pth'
        self.run_flag = True
        self.img_name = 'test.jpg'
        self.device = 'cuda' 
        self.net.to(device=self.device)
        self.net.load_state_dict(torch.load(self.model, map_location=self.device))
        self.got_image = False


    def run(self):
        while self.run_flag:
            logging.info("AHHHHHHHHH")
            if self.got_image:    
                mask = self.predict_img(net=self.net, full_img=self.full_img, scale_factor=0.2, out_threshold=0.5, device=self.device)
                self.got_image = False
            else:
                self.msleep(100)


    @pyqtSlot(np.ndarray)
    def get_image(self, cv_img2):
        self.full_img = cv_img2
        self.got_image = True
    
    def stop(self):
        self.run_flag = False

    def predict_img(self, net, full_img, device, scale_factor=0.2, out_threshold=0.7):
        self.net.eval()
        logging.info(full_img.shape)
        full_img = Image.fromarray(full_img)
        img = torch.from_numpy(BasicDataset.preprocess(full_img, scale_factor, is_mask=False))
        img = img.unsqueeze(0)
        img = img.to(device=device, dtype=torch.float32)

        with torch.no_grad():
            logging.info("BEFORE NET")
            output = net(img)
            logging.info("AFTER NET")
            
            probs = torch.sigmoid(output)[0]

            tf = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((full_img.size[1], full_img.size[0])),
                transforms.ToTensor()
            ])
            t1 = time.perf_counter()
            full_mask = tf(probs.cpu()).squeeze()
            logging.info('%.5f',t1-time.perf_counter())
        
        mask = F.one_hot(full_mask.argmax(dim=0), net.n_classes).permute(2, 0, 1).numpy()
        self.change_pixmap_signal_ai.emit(mask)
        
        result = self.mask_to_image(mask) 
        result.save(self.img_name)
        
    def mask_to_image(self, mask: np.ndarray):
        # print(mask.ndim)
        # if mask.ndim == 2:
        #     return Image.fromarray((mask * 255).astype(np.uint8))
        if mask.ndim == 3:
            return Image.fromarray((np.argmax(mask, axis=0) * 255 / mask.shape[0]).astype(np.uint8))



