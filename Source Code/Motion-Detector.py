from flask import Flask, render_template, Response, request
from flask_cors import CORS
import cv2
import time
import glob
import os
import base64
import numpy as np
from threading import Thread
import sys
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Alert function from emailing.py
from emailing import Alert

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__, template_folder='../Website-Code')
CORS(app, origins=["https://munibsmotiondetector.netlify.app"])  # Replace with your Netlify domain

# Initialize variables
InitialFrame = None
StatusList = []
count = 1
motion_detected = False
recipient_email = None

# Function to clean up images
def CleanImages():
    images = glob.glob("./images/*.png")  # Use the relative path to the images folder
    for image in images:
        os.remove(image)
    logging.info("Cleaned up images")

# Function to process a single frame
def process_frame(frame):
    global InitialFrame, StatusList, count, motion_detected

    # Decode the image
    img_data = base64.b64decode(frame.split(',')[1])
    np_img = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    Status = False

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
    logging.debug(f"Number of contours found: {len(contours)}")

    for contour in contours:
        contour_area = cv2.contourArea(contour)
        logging.debug(f"Contour area: {contour_area}")
        if contour_area < 5000:
            continue

        x, y, width, height = cv2.boundingRect(contour)
        rectangle = cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)
        logging.debug(f"Motion detected: {rectangle.any()}")

        if rectangle.any():
            Status = True
            motion_detected = True
            image_path = f"./images/{count}.png"  # Use the relative path to the images folder
            cv2.imwrite(image_path, frame)
            count += 1
            logging.info(f"Saved image {image_path}")

            AllImages = glob.glob("./images/*.png")  # Use the relative path to the images folder
            if AllImages:
                index = int(len(AllImages) / 2)
                FinalImage = AllImages[index]
            else:
                FinalImage = None

    StatusList.append(Status)
    StatusList = StatusList[-2:]
    logging.debug(f"StatusList: {StatusList}")

    if motion_detected and StatusList[0] == 1 and StatusList[1] == 0 and FinalImage:
        logging.info("Motion ended, sending alert...")
        if recipient_email:
            # Call the Alert function with recipient email and image path
            Alert(recipient_email, FinalImage)
        cleanThread = Thread(target=CleanImages)
        cleanThread.daemon = True
        cleanThread.start()

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
