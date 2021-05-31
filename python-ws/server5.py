from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import base64
import cv2
import numpy as np
import time
import lane2
import _thread as thread

from PIL import ImageGrab
import win32gui

import json

from tracker import *

# Create tracker object
tracker = EuclideanDistTracker()

# import cvlib as cv
# from cvlib.object_detection import draw_bbox

# SSD model defenition
net = cv2.dnn_DetectionModel('model/frozen_inference_graph.pb', 'model/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

borderX = borderY = 5
startX = 240
startY = 128
cameraSizeX = cameraSizeY = 256

handle_position = None
connection_active = False

focal_length = 50

car_bottom_y = cameraSizeY // 2

is_night = True

def get_handle_position(windows_title="open-cv-car"):
    windows_list = []
    toplist = []

    def enum_win(hwnd, result):
        win_text = win32gui.GetWindowText(hwnd)
        windows_list.append((hwnd, win_text))

    win32gui.EnumWindows(enum_win, toplist)

    game_hwnd = None
    for (hwnd, win_text) in windows_list:
        if win_text.startswith(windows_title):
            print(hwnd, win_text)
            game_hwnd = hwnd
    print(game_hwnd)

    global handle_position
    
    handle_position = win32gui.GetWindowRect(game_hwnd)
    print(handle_position)
    return handle_position

def grab_image():
    global handle_position

    # Take screenshot
    screenshot = ImageGrab.grab(handle_position)
    return np.array(screenshot)

def crop_image(screenshot):
    screenshot = screenshot[startY + borderY:startY + cameraSizeY - borderY, startX + borderX:startX + cameraSizeX - borderX]
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

    return screenshot

def get_distance(bbox, ref_length):
    return ref_length * focal_length / bbox[3]


class SimpleEcho(WebSocket):

    def handleMessage(self):
        # screenshot = []

        def send_response(response):
            self.sendMessage(json.dumps(response))

        print('message', self.data.decode("utf-8"))
        if self.data.decode("utf-8").startswith('is_night'):
            global is_night
            is_night = self.data.decode("utf-8")[-1] == '1'
            print('is_night', is_night)

        if self.data.decode("utf-8") == 'start':
            def run(*args):
                frame_counter = 0
                response = {}

                global connection_active
                while connection_active:

                    frame_counter += 1
                    
                    screenshot = grab_image()
                    screenshot = crop_image(screenshot)

                    # screenshot = screenshot[startY:startY + borderY * 2 + cameraSizeY, startX:startX + borderX * 2 + cameraSizeX]
                    # bbox, label, conf = cv.detect_common_objects(screenshot, enable_gpu=True)
                    # yolo_screenshot = draw_bbox(screenshot, bbox, label, conf)
                    
                    laned_screenshot, gray_roi = lane_detection(screenshot, response)

                    if ('stop' in response and response['stop'] > 0 or 'car' in response and response['car'] > 0 or frame_counter % 5 == 0):
                        object_screenshot = object_detection(screenshot, response)
                        
                        screenshot = cv2.addWeighted(laned_screenshot, 0.5, object_screenshot, 0.5, 0)

                    send_response(response)


                    cv2.line(screenshot, (0, car_bottom_y), (cameraSizeX, car_bottom_y), (255, 255, 255), 1)
 
                    cv2.imshow("Screen", screenshot)
                    if len(gray_roi) > 0:
                        cv2.imshow("Gray ROI", gray_roi)

                    key = cv2.waitKey(1)
                    if key == 27:
                        break

                cv2.destroyAllWindows()
            
            def lane_detection(screenshot, response):
                gray_roi = []

                try:
                    global is_night
                    vert_shift, screenshot, gray_roi = lane2.process(screenshot, roi_height=(car_bottom_y / cameraSizeY), is_night_conditions=is_night)
                    
                    response['vert_shift'] = vert_shift
                except:
                    pass

                return screenshot, gray_roi

            def object_detection(screenshot, response={}, allow_class_ids=[13, 3]):
                class_to_name = {
                    13: { 'name': 'stop', 'refer_height': 2000, 'color': (0, 255, 0) },
                    3: { 'name': 'car', 'refer_height': 3000, 'color': (255, 0, 0) }
                }

                response['stop'] = 0
                response['car'] = 0
                response['stopId'] = -1
                response['carId'] = -1

                try:
                    classes, confidences, boxes = net.detect(screenshot, confThreshold=0.3)
                    classesFlatten = classes.flatten()

                    if any(c in classesFlatten for c in allow_class_ids):
                        allowed_boxes = [boxes[r] for r in range(len(classesFlatten)) if classesFlatten[r] in allow_class_ids]

                        tracked_objs = tracker.update(allowed_boxes)
                        
                        for inx, (classId, confidence, box) in enumerate([(cl, co, b) for cl, co, b in zip(classesFlatten, confidences.flatten(), boxes) if cl in allow_class_ids]):
                            class_name = class_to_name[classId.item()]
                            distance = round(get_distance(box, class_name['refer_height']) / 1000, 2)
                            print(classId, confidence, box, box[2] * box[3], box[2] * box[3] * confidence, distance)


                            dist_text = f'{distance}'
                            class_text = f'{class_name["name"]}{tracked_objs[inx][-1]}'
                            font = cv2.FONT_HERSHEY_PLAIN
                            
                            dist_textsize = cv2.getTextSize(dist_text, font, 1.2, 2)[0]
                            class_textsize = cv2.getTextSize(class_text, font, 1.2, 2)[0]


                            # get coords based on boundary
                            textX = box[0] + box[2] // 2 - dist_textsize[0] // 2
                            textY = box[1] + box[3] // 2 + dist_textsize[1] // 2

                            class_textX = box[0] + box[2] // 2 - class_textsize[0] // 2
                            class_textY = box[1] + box[3] // 2 + class_textsize[1] // 2

                            # print(textsize, textX, textY, box)
                            cv2.putText(screenshot, dist_text, (textX, int(textY - 1.5 * dist_textsize[1])), font, 1.2, (255, 0, 0), 2)
                            cv2.putText(screenshot, class_text, (class_textX, int(class_textY + 1.5 * class_textsize[1])), font, 1.2, (255, 0, 0), 2)
                            cv2.rectangle(screenshot, box, color=class_name['color'])

                            # response['objects'][class_name['name']] = { 'area': int(box[2] * box[3]), 'conf_area': int(box[2] * box[3] * confidence) }

                            response[class_name['name']] = int(box[2] * box[3])
                            response[class_name['name'] + "Id"] = tracked_objs[inx][-1]

                            if class_name['name'] == 'car':
                                global car_bottom_y
                                car_bottom_y = box[1] + box[3]
                except:
                    pass

                return screenshot
                
            thread.start_new_thread(run, ())
        else:
            print(len(self.data))
            
            jpg_as_np = np.frombuffer(self.data, dtype=np.uint8)
            img = cv2.imdecode(jpg_as_np, cv2.IMREAD_COLOR)         

            try: 
                self.sendMessage(str(lane2.process(img)))
            except:
                pass

    def handleConnected(self):
        print(self.address, 'connected')
        global connection_active
        connection_active = True
        
    def handleClose(self):
        print(self.address, 'closed')
        global connection_active
        connection_active = False

get_handle_position()
server = SimpleWebSocketServer('localhost', 12345, SimpleEcho)
server.serveforever()
