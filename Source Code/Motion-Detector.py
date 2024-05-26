import cv2
import time
import glob
import os
from threading import Thread
from flask import Flask, render_template, request, Response

app = Flask(__name__)

video = cv2.VideoCapture(0)
time.sleep(1)

activate_motion_detector = False

def motion_detection():
    global activate_motion_detector

    while True:
        if not activate_motion_detector:
            continue

        ret, frame = video.read()
        cv2.imshow("MyVid", frame)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    video.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(motion_detection(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/submit', methods=['POST'])
def submit():
    global activate_motion_detector

    email = request.form['email']
    print("Received email:", email)  # Debugging line
    activate_motion_detector = True
    return "Motion detector activated. You will receive notifications via email."

if __name__ == "__main__":
    app.run(debug=True)
