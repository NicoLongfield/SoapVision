import csv
import sys
import os
import time
class csv_data_export():
    def __init__(self):
        self.headers = ['Time', 'Image', 'Mask', 'Temp', 'Hum', 'Lux', 'R', 'G', 'B']
        self.path = '/home/jetson_user/Projet/Images/'
        self.csv_filename = time.strftime('%d_%b_%Y') + '.csv'
        
    def _append_to_csv(data_to_append):
        path__ = self.path + self.csv_filename
        no_headers = not os.path.exists(path__) or os.stat(path__).st_size == 0
        with open(csv_filename, 'a', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            if no_headers:
                writer.writerow(self.headers)
            writer.writerow(data_to_append)
