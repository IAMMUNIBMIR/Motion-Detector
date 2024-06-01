import cv2
import time
import glob
import os
from flask import Flask, render_template, Response, request
from threading import Thread
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from emailing import send_email

app = Flask(__name__, template_folder='../Website-Code')

# Create directory for storing images if it doesn't exist
if not os.path.exists('static/images'):
    os.makedirs('static/images')

video = cv2.VideoCapture(0)
time.sleep(1)

InitialFrame = None
StatusList = []
count = 1
recipient_email = None  # Global variable to store recipient email

def CleanImages():
    images = glob.glob("static/images/*.png")
    for image in images:
        os.remove(image)

def generate_frames():
    global InitialFrame, StatusList, count

    while True:
        Status = False
        check, frame = video.read()
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grayFrameBlur = cv2.GaussianBlur(grayFrame, (21, 21), 0)

        if InitialFrame is None:
            InitialFrame = grayFrameBlur

        FrameDiff = cv2.absdiff(InitialFrame, grayFrameBlur)
        ThreshFrame = cv2.threshold(FrameDiff, 60, 255, cv2.THRESH_BINARY)[1]
        DilatedFrame = cv2.dilate(ThreshFrame, None, iterations=2)

        contours, _ = cv2.findContours(DilatedFrame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            rectangle = cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)

            if rectangle.any():
                Status = True
                image_path = f"static/images/{count}.png"
                cv2.imwrite(image_path, frame)
                count += 1

                AllImages = glob.glob("static/images/*.png")
                index = int(len(AllImages) / 2)
                FinalImage = AllImages[index]

        StatusList.append(Status)
        StatusList = StatusList[-2:]

        if StatusList[0] == 1 and StatusList[1] == 0 and recipient_email:
            EmailThread = Thread(target=send_email, args=(recipient_email, FinalImage))
            EmailThread.daemon = True
            cleanThread = Thread(target=CleanImages)
            cleanThread.daemon = True

            EmailThread.start()
            cleanThread.start()

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('body.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/submit', methods=['POST'])
def submit():
    global recipient_email
    recipient_email = request.form.get('email')
    print("Received email:", recipient_email)
    return "Email submitted successfully"

if __name__ == '__main__':
    app.run(debug=True)
