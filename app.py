from flask import Flask, Response, request, render_template
import cv2
import numpy as np
import os
import glob
import face_recognition
import time
import datetime
import re

app = Flask(__name__)

last_detected_person = None
last_detected_time = {}

class SimpleFacerec:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_folders = []
        self.frame_resizing = 0.25

    def load_encoding_images(self, images_path):
        images = glob.glob(os.path.join(images_path, "*.*"))

        print(f"{len(images)} encoding images found.")

        for img_path in images:
            try:
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Failed to load image: {img_path}")
                    continue

                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                folder_name = os.path.basename(os.path.dirname(img_path))
                filename, _ = os.path.splitext(os.path.basename(img_path))

                img_encoding = face_recognition.face_encodings(rgb_img)[0]

                self.known_face_encodings.append(img_encoding)
                self.known_face_names.append(filename)
                self.known_face_folders.append(folder_name)
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")

        print("Encoding images loaded")

    def detect_known_faces(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        entry_log = {}
        face_names = []
        face_folders = []

        for face_encoding, face_loc in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.55)  # Adjust threshold
            name = "Unknown"
            folder = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                if face_distances[best_match_index] <= 0.50:  # Adjust minimum face distance threshold
                    name = self.known_face_names[best_match_index]
                    folder = self.known_face_folders[best_match_index]

                    if name not in entry_log:
                        entry_log[name] = datetime.datetime.now()

            face_names.append(name)
            face_folders.append(folder)

        face_locations = np.array(face_locations) / self.frame_resizing
        return face_locations.astype(int), face_names, face_folders, entry_log

entry_log = {}
known_people = set()
last_detected_time = {}
def enough_time_passed(name):
    current_time = time.time()
    if name in last_detected_time:
        last_time = last_detected_time[name]
        return current_time - last_time > 120  # 120 seconds = 2 minutes
    return True

@app.route('/video_feed', methods=['POST'])
def video_feed():
    global last_detected_time

    try:
        # Getting the image from the POST request
        image = request.files['image'].read()
        nparr = np.fromstring(image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Getting the camera ID from the POST request
        camera_id = request.form.get('camera_id')

        face_locations, face_names, face_folders, new_entry_log = sfr.detect_known_faces(frame)

        for face_loc, name, folder in zip(face_locations, face_names, face_folders):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 200, 0), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

            current_time = time.time()

            if name != "Unknown":
                if name not in known_people or enough_time_passed(name):
                    known_people.add(name)
                    last_detected_time[name] = current_time

                    log_entry = f"{folder}: {name} entered at: {time.ctime(current_time)} (Camera ID: {camera_id})"
                    with open(output_file, 'a') as log_file:
                        log_file.write(log_entry + '\n')

        ret, jpeg = cv2.imencode('.jpg', frame)
        return Response(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n',
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        print("Error:", e)
        return Response("Error", status=500)


@app.route('/log_entries')
def log_entries():
    global entry_log

    try:
        log_entries = []  # Initialize an empty list to store the log entries
        # Reading log entries from the output file and populate log_entries list
        with open(output_file, 'r') as log_file:
            for line in log_file:
                entry_info = re.findall(r'(.+): (.+) entered at: (.+) \(Camera ID: (.+)\)', line.strip())
                if entry_info:
                    folder, name, timestamp_str, camera_id = entry_info[0]
                    timestamp = datetime.datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
                    log_entries.append({'folder': folder, 'name': name, 'timestamp': timestamp, 'camera_id': camera_id})

        # Sort log entries by timestamp in descending order
        log_entries.sort(key=lambda x: x['timestamp'], reverse=True)

        return render_template('log_entries.html', log_entries=log_entries)
    except Exception as e:
        print("Error:", e)
        return render_template('error_page.html', error_message=str(e))

@app.route('/get_log_entries')
def get_log_entries():
    try:
        start_time_str = request.args.get('start_time', '')
        end_time_str = request.args.get('end_time', '')
        camera_id = request.args.get('camera_id', '')

        # Convert the start and end time strings to datetime objects
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

        log_entries = []  # Initialize an empty list to store the log entries
        # Reading log entries from the output file and filter based on the time range and camera ID
        with open(output_file, 'r') as log_file:
            for line in log_file:
                folder, name, timestamp_str, entry_camera_id = re.findall(r'(.+): (.+) entered at: (.+) \(Camera ID: (.+)\)', line.strip())[0]
                timestamp = datetime.datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')

                # Filter the log entry based on the time range and camera ID
                if start_time <= timestamp <= end_time and (camera_id.lower() == "all" or camera_id == entry_camera_id):
                    log_entries.append({'folder': folder, 'name': name, 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'camera_id': entry_camera_id})

        # Sort log entries by timestamp in descending order
        log_entries.sort(key=lambda x: x['timestamp'], reverse=True)

        return render_template('log_entries.html', log_entries=log_entries)
    except Exception as e:
        print("Error:", e)
        return render_template('error_page.html', error_message=str(e))

if __name__ == '__main__':
    sfr = SimpleFacerec()
    sfr.load_encoding_images("Authorized/")
    sfr.load_encoding_images("Restricted/")

    known_people = set()  # Initialize the set of known people

    last_detected_time = {}  # Initialize the last_detected_time dictionary

    entry_log = {}
    output_folder = 'output_logs'
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_folder, f'output_log_{timestamp}.txt')

    app.run(host='0.0.0.0', port=5050, debug=True)