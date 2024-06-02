from flask import Flask, render_template, Response, request
from flask_cors import CORS
import cv2
import time
import glob
import os
from threading import Thread
import sys
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from emailing import Alert

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__, template_folder='../Website-Code')
CORS(app, origins=["https://munibsmotiondetector.netlify.app"])  # Replace with your Netlify domain

# Open the video capture device
video = cv2.VideoCapture(0)
if not video.isOpened():
    logging.error("Failed to open video capture device.")
else:
    logging.info("Video capture device opened successfully.")

# Delay to allow camera to initialize
time.sleep(1)

# Initialize variables
InitialFrame = None
StatusList = []
count = 1
motion_detected = False

# Function to clean up images
def CleanImages():
    images = glob.glob("../images/*.png")  # Use the relative path to the images folder
    for image in images:
        os.remove(image)
    logging.info("Cleaned up images")

# Generator function to generate frames
def generate_frames():
    global InitialFrame, StatusList, count, motion_detected

    while True:
        Status = False
        check, frame = video.read()

        if not check:
            logging.error("Failed to capture frame. Retrying...")
            time.sleep(0.1)  # Short delay before retrying
            continue

        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grayFrameBlur = cv2.GaussianBlur(grayFrame, (21, 21), 0)

        if InitialFrame is None:
            InitialFrame = grayFrameBlur
            logging.debug("Set initial frame")
            continue

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
                image_path = f"../images/{count}.png"  # Use the relative path to the images folder
                cv2.imwrite(image_path, frame)
                count += 1
                logging.info(f"Saved image {image_path}")

                AllImages = glob.glob("../images/*.png")  # Use the relative path to the images folder
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
            EmailThread = Thread(target=Alert, args=(FinalImage,))
            EmailThread.daemon = True
            cleanThread = Thread(target=CleanImages)
            cleanThread.daemon = True

            EmailThread.start()
            cleanThread.start()

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Endpoint to handle email submission
@app.route('/submit', methods=['POST'])
def submit_email():
    email = request.form.get('email')  # Get the email from the request data
    # Perform any necessary logic with the email (e.g., activate motion detector)
    # Here you can add logic to activate the motion detector based on the received email
    # For example:
    logging.info(f"Received email for activation: {email}")
    # Return a response indicating success
    return 'Email submitted successfully'

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
