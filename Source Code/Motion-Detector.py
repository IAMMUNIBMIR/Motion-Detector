from flask import Flask, render_template, request
from flask_cors import CORS
import cv2
import glob
import os
import base64
import numpy as np
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

# Set the base directory for images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')

# Ensure the image directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

# Cooldown period settings
cooldown_time = 30  # Cooldown time in seconds
last_alert_time = 0  # Last alert time

# Frame skip settings
frame_skip = 45  
frame_count = 0  # Counter for frames

# Function to clean up images
def CleanImages():
    images = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
    for image in images:
        os.remove(image)
    logging.info("Cleaned up images")

# Function to process a single frame
def process_frame(frame):
    global InitialFrame, motion_detected, recipient_email, latest_image_path, last_alert_time, frame_count

    current_time = time.time()  # Get the current time

    img_data = base64.b64decode(frame.split(',')[1])
    np_img = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if frame_count % frame_skip != 0:  # Skip frames based on frame_skip
        frame_count += 1
        return

    frame_count = 0  # Reset frame count

    grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    grayFrameBlur = cv2.GaussianBlur(grayFrame, (21, 21), 0)

    if InitialFrame is None:
        InitialFrame = grayFrameBlur
        logging.debug("Set initial frame")
        return

    FrameDiff = cv2.absdiff(InitialFrame, grayFrameBlur)
    ThreshFrame = cv2.threshold(FrameDiff, 25, 255, cv2.THRESH_BINARY)[1]
    DilatedFrame = cv2.dilate(ThreshFrame, None, iterations=2)

    contours, _ = cv2.findContours(DilatedFrame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < 1000:
            continue

        x, y, width, height = cv2.boundingRect(contour)
        rectangle = cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)

        if rectangle.any():
            motion_detected = True
            image_path = os.path.join(IMAGE_DIR, f"detected_motion.png")
            cv2.imwrite(image_path, frame)
            logging.info(f"Saved image {image_path}")
            latest_image_path = image_path

    if motion_detected and current_time - last_alert_time > cooldown_time:
        logging.info("Motion detected, sending alert...")
        if recipient_email:
            logging.info("Process started, sending alert...")
            if os.path.exists(latest_image_path):
                # Call the Alert function with recipient email and latest image path
                Alert(recipient_email, latest_image_path)
                logging.info(f"Process finished, alert sent for {latest_image_path}")
                last_alert_time = current_time  # Update the last alert time
            else:
                logging.error(f"File not found: {latest_image_path}")
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
    return 'Email received', 200

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
