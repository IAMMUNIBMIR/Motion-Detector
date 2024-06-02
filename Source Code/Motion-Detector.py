from flask import Flask, render_template, Response, request
from flask_cors import CORS
import cv2
import glob
import os
import base64
import numpy as np
from threading import Thread
import logging
import sys
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from emailing import Alert  # Import the Alert function

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='../Website-Code')
CORS(app, origins=["https://munibsmotiondetector.netlify.app"])  

# Initialize variables
InitialFrame = None
motion_detected = False
recipient_email = None
latest_image_path = None

# Function to clean up images
def CleanImages():
    images = glob.glob("./images/*.png")
    for image in images:
        os.remove(image)
    logging.info("Cleaned up images")

# Function to process a single frame
def process_frame(frame):
    global InitialFrame, motion_detected, recipient_email, latest_image_path

    img_data = base64.b64decode(frame.split(',')[1])
    np_img = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    grayFrameBlur = cv2.GaussianBlur(grayFrame, (21, 21), 0)

    if InitialFrame is None:
        InitialFrame = grayFrameBlur
        logging.debug("Set initial frame")
        return

    FrameDiff = cv2.absdiff(InitialFrame, grayFrameBlur)
    ThreshFrame = cv2.threshold(FrameDiff, 60, 255, cv2.THRESH_BINARY)[1]
    DilatedFrame = cv2.dilate(ThreshFrame, None, iterations=2)

    contours, _ = cv2.findContours(DilatedFrame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < 5000:
            continue

        x, y, width, height = cv2.boundingRect(contour)
        rectangle = cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)

        if rectangle.any():
            motion_detected = True
            image_path = f"./images/{time.time()}.png"
            cv2.imwrite(image_path, frame)
            logging.info(f"Saved image {image_path}")
            latest_image_path = image_path

    if motion_detected:
        logging.info("Motion detected, sending alert...")
        if recipient_email:
            logging.info("Process started, sending alert...")
            # Call the Alert function with recipient email and image path
            Alert(recipient_email, latest_image_path)
            logging.info("Process finished, alert sent")
        motion_detected = False  # Reset motion detection flag

    if not motion_detected:
        InitialFrame = grayFrameBlur


# Route to process frames
@app.route('/process_frame', methods=['POST'])
def receive_frame():
    frame_data = request.json['frame']
    process_frame(frame_data)
    return 'Frame received', 200

# Route to receive email for alerts
@app.route('/submit', methods=['POST'])
def submit_email():
    global recipient_email
    recipient_email = request.form['email']
    logging.info(f"Recipient email set to: {recipient_email}")
    return 'Email received', 200, recipient_email

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
