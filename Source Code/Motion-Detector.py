import cv2
import time
import glob
import os
from emailing import Alert
from threading import Thread
from flask import Flask, render_template, Response

app = Flask(__name__)

video = cv2.VideoCapture(0)
time.sleep(1)

InitialFrame = None
StatusList = []
count = 1
activate_motion_detector = True  # Automatically activate motion detector

def CleanImages():
    images = glob.glob("images/*.png")
    for image in images:
        os.remove(image)

def motion_detection():
    global InitialFrame, count, activate_motion_detector

    while True:
        if not activate_motion_detector:
            continue

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
                cv2.imwrite(f"images/{count}.png", frame)
                count += 1

                AllImages = glob.glob("images/*.png")
                index = int(len(AllImages) / 2)
                FinalImage = AllImages[index]

        StatusList.append(Status)
        StatusList = StatusList[-2:]

        if StatusList[0] == 1 and StatusList[1] == 0:
            EmailThread = Thread(target=Alert, args=(FinalImage,))
            EmailThread.daemon = True
            cleanThread = Thread(target=CleanImages)
            cleanThread.daemon = True

            EmailThread.start()
            cleanThread.start()

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

if __name__ == "__main__":
    app.run(debug=True)
