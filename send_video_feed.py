import cv2
import requests

# Capture video from webcam(0)
cap = cv2.VideoCapture(0)

# Define the URL for Flask app's /video_feed endpoint
url = 'http://localhost:5050/video_feed'

# Define the camera ID (You can set a unique camera ID based on your requirements)
camera_id = 'Camera001'

while True:
    ret, frame = cap.read()

    # Encoding frame
    _, img_encoded = cv2.imencode('.jpg', frame)

    # Converting the JPEG bytes to a NumPy array
    img_array = img_encoded.tobytes()

    # Creating a multipart-formdata request with the image data and camera ID
    files = {'image': ('image.jpg', img_array, 'image/jpeg')}
    data = {'camera_id': camera_id}

    try:
        # Making a POST request to the Flask app's /video_feed endpoint
        response = requests.post(url, files=files, data=data)

        # Printing the response content
        print(response.content)
    except requests.exceptions.RequestException as e:
        print('Error sending request:', e)

    # Displaying the frame
    cv2.imshow('Video Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
