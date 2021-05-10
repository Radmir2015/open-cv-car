import cv2 as cv
import time

net = cv.dnn_DetectionModel('model/frozen_inference_graph.pb', 'model/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

frame = cv.imread('stop1.jpg')

start = time.time()
classes, confidences, boxes = net.detect(frame, confThreshold=0.5)
end = time.time()

print(end - start, 'ms')

for classId, confidence, box in zip(classes.flatten(), confidences.flatten(), boxes):
    print(classId, confidence)
    cv.rectangle(frame, box, color=(0, 255, 0))

cv.imshow('out', frame)
cv.waitKey()
