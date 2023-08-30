import socket
import cv2
import pickle
import struct
import threading
import keyboard

quit_key = 'q'

config_file = "config.txt"
config = {}
with open(config_file, "r") as file:
    for line in file:
        key, value = line.strip().split("=")
        config[key] = value

host = config.get('host')
port = int(config.get('port'))
camera_name = config.get('camera_name')

if host is None or port is None or camera_name is None:
    raise ValueError("Configuration values missing in config.txt")

stop_sending = False

def send_frame(ClientSocket, camera_name):
    global stop_sending
    vid = cv2.VideoCapture(0)
    while vid.isOpened() and not stop_sending:
        ret, frame = vid.read()
        if not ret:
            break
        frame = cv2.resize(frame, (320, 240))

        cv2.imshow('Sending Frame - ' + camera_name, frame)
        cv2.waitKey(1)  # Wait for a short time to update the display

        data = pickle.dumps((camera_name, frame))
        message = struct.pack("Q", len(data)) + data
        ClientSocket.sendall(message)

    vid.release()
    cv2.destroyAllWindows()

    if stop_sending:
        cv2.destroyWindow('Sending Frame - ' + camera_name)

def key_listener():
    global stop_sending
    keyboard.wait(quit_key)
    stop_sending = True

key_thread = threading.Thread(target=key_listener)
key_thread.daemon = True
key_thread.start()

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Waiting for connection')
try:
    ClientSocket.connect((host, port))
except socket.error as e:
    print(str(e))

send_frame(ClientSocket, camera_name)
ClientSocket.close()
