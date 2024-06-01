import cv2
import time
import glob
import os
from flask import Flask, render_template, Response
from threading import Thread
from emailing import Alert

app = Flask(__name__, template_folder='../Website-Code')

video = cv2.VideoCapture(0)
time.sleep(1)

InitialFrame = None
StatusList = []
count = 1
motion_detected = False

def CleanImages():
    images = glob.glob("static/images/*.png")
    for image in images:
        os.remove(image)

def generate_frames():
    global InitialFrame, StatusList, count, motion_detected

    while True:
        Status = False
        check, frame = video.read()
        
        if not check:
            print("Failed to capture frame")
            continue
        
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grayFrameBlur = cv2.GaussianBlur(grayFrame, (21, 21), 0)

        if InitialFrame is None:
            InitialFrame = grayFrameBlur
            continue
        
        FrameDiff = cv2.absdiff(InitialFrame, grayFrameBlur)
        ThreshFrame = cv2.threshold(FrameDiff, 60, 255, cv2.THRESH_BINARY)[1]
        DilatedFrame = cv2.dilate(ThreshFrame, None, iterations=2)

        # Display intermediate frames for debugging
        cv2.imshow("Gray Frame", grayFrame)
        cv2.imshow("Blurred Frame", grayFrameBlur)
        cv2.imshow("Frame Difference", FrameDiff)
        cv2.imshow("Threshold Frame", ThreshFrame)
        cv2.imshow("Dilated Frame", DilatedFrame)

        contours, _ = cv2.findContours(DilatedFrame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Number of contours found: {len(contours)}")

        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            rectangle = cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)
            print(f"Motion detected: {rectangle.any()}")

            if rectangle.any():
                Status = True
                motion_detected = True
                image_path = f"static/images/{count}.png"
                cv2.imwrite(image_path, frame)
                count += 1

                AllImages = glob.glob("static/images/*.png")
                index = int(len(AllImages) / 2)
                FinalImage = AllImages[index]

        StatusList.append(Status)
        StatusList = StatusList[-2:]
        print(f"StatusList: {StatusList}")

        if motion_detected and StatusList[0] == 1 and StatusList[1] == 0:
            print("Motion ended, sending alert...")
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
