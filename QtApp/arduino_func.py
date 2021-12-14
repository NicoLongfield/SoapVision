import serial 
import time
import json
import threading
#arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
#class ArduinoSensors():

#   def __init__(self):
#      print("Arduino init...")
arduino = serial.Serial(
    port = '/dev/ttyACM0',
    baudrate = 115200,
    bytesize = serial.EIGHTBITS,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    timeout = 5,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False,
    writeTimeout = 2
)
arduino.reset_input_buffer()
#       self.running = False


def update_serial():
    while True:
        data = arduino.readline().decode("utf-8")
        try:
            dict_json = json.loads(data)
            print(dict_json)
        except json.JSONDecodeError as e:
            dict_json = {}


#
#def stop_serial(self):
#    self.running = False
#    self.read_thread.join()


def print_to_inf(dict_args):
    while True:
        print(dict_args)
        time.sleep(5)

# loop = asyncio.get_event_loop()
if __name__ == "__main__":
 #   arduino_serial = threading.Thread(target=update_serial(), kwar)
    update_serial()
  #  while True:
  #      print(arduino_serial)
   #     time.sleep(2)

# import serial 
# import time
# import json
# import threading
# #arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
# #class ArduinoSensors():

# #   def __init__(self):
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
#             global json_data = dict_json
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
#     arduino_serial.start()
#   #  while True:
#   #      print(arduino_serial)
#    #     time.sleep(2)
