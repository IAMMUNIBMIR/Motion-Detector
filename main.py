import cv2
import time
from emailing import Alert


video = cv2.VideoCapture(0)
time.sleep(1)

InitialFrame = None
StatusList = []

while True:

    Status = False
    check, frame = video.read()
    grayFrame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    grayFrameBlur = cv2.GaussianBlur(grayFrame, (21,21), 0)

    if InitialFrame is None:
        InitialFrame = grayFrameBlur

    FrameDiff = cv2.absdiff(InitialFrame,grayFrameBlur)
    ThreshFrame = cv2.threshold(FrameDiff, 60, 255, cv2.THRESH_BINARY)[1]
    DilatedFrame = cv2.dilate(ThreshFrame, None, iterations=2)
    cv2.imshow("Video", DilatedFrame)

    contours, check = cv2.findContours(DilatedFrame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < 5000:
            continue

        x,y,width,height = cv2.boundingRect(contour)
        rectangle = cv2.rectangle(frame, (x,y), (x+width,y+height), (0,255,0), 3)

        if rectangle.any():
            Status = True

    StatusList.append(Status)
    StatusList = StatusList[-2:]

    if StatusList[0] == 1 and StatusList[1] == 0:
        Alert()
        
    cv2.imshow("MyVid", frame)
    key = cv2.waitKey(1)

    if key == ord("q"):
        break


video.release()

