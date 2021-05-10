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

# import cvlib as cv
# from cvlib.object_detection import draw_bbox

# SSD model defenition
net = cv2.dnn_DetectionModel('model/frozen_inference_graph.pb', 'model/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

borderX = borderY = 5
startX = 16 
startY = 128
cameraSizeX = cameraSizeY = 256

handle_position = None
connection_active = False


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
    
    handle_position = win32gui.GetWindowRect(game_hwnd)
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


class SimpleEcho(WebSocket):

    def handleMessage(self):
        # screenshot = []

        def send_response(response):
            self.sendMessage(json.dumps(response))

        print('message', self.data.decode("utf-8"))
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
                    

                    screenshot = lane_detection(screenshot, response)

                    if ('stop' in response and response['stop'] > 0 or frame_counter % 5 == 0):
                        screenshot = object_detection(screenshot, response)

                    send_response(response)
 
                    cv2.imshow("Screen", screenshot)

                    key = cv2.waitKey(1)
                    if key == 27:
                        break

                cv2.destroyAllWindows()
            
            def lane_detection(screenshot, response):
                try:
                    vert_shift, screenshot = lane2.process(screenshot)
                    
                    # self.sendMessage(str(vert_shift))

                    response['vert_shift'] = vert_shift
                except:
                    pass

                return screenshot

            def object_detection(screenshot, response={}, allow_class_ids=[13, 3]):
                class_to_name = { 13: 'stop', 3: 'car' }
                response['objects'] = { 'stop': { 'area': 0, 'conf_area': 0 }, 'car': { 'area': 0, 'conf_area': 0 } }
                response['stop'] = 0
                # while True:
                try:
                    classes, confidences, boxes = net.detect(screenshot, confThreshold=0.3)
                    classesFlatten = classes.flatten()
                    # print(classesFlatten, 12 in classesFlatten)

                    if any(c in classesFlatten for c in allow_class_ids):
                        # print("classes", classes)
                        # response['objects'] = {}
                        response['objects'] = { 'stop': { 'area': 0, 'conf_area': 0 }, 'car': { 'area': 0, 'conf_area': 0 } }
                        response['stop'] = 0
                        
                        for classId, confidence, box in zip(classesFlatten, confidences.flatten(), boxes):
                            if classId in allow_class_ids:
                                print(classId, confidence, box, box[2] * box[3], box[2] * box[3] * confidence)
                                cv2.rectangle(screenshot, box, color=(0, 255, 0))

                                response['objects'][class_to_name[classId.item()]] = { 'area': int(box[2] * box[3]), 'conf_area': int(box[2] * box[3] * confidence) }
                                response['stop'] = int(box[2] * box[3])
                except:
                    pass

                return screenshot
                
            thread.start_new_thread(run, ())
            # thread.start_new_thread(object_detection, ())
        else:
            # echo message back to client
            print(len(self.data))
            
            # jpg_original = base64.b64decode(self.data)
            jpg_as_np = np.frombuffer(self.data, dtype=np.uint8)
            img = cv2.imdecode(jpg_as_np, cv2.IMREAD_COLOR)         
            # print('info', jpg_original, jpg_as_np, img)

            # cv2.imwrite('file.png', img)
            # cv2.imshow('img', img)
            try: 
                self.sendMessage(str(lane2.process(img)))
            except:
                pass
            # self.sendMessage(self.data)
            # sleep(5)
            # cv2.waitKey(1)
            # cv2.destroyAllWindows()

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
