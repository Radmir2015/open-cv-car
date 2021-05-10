from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import base64
import cv2
import numpy as np
import time
import lane2
import _thread as thread

from PIL import ImageGrab
import win32gui

# import cvlib as cv
# from cvlib.object_detection import draw_bbox

# SSD model defenition
net = cv2.dnn_DetectionModel('model/frozen_inference_graph.pb', 'model/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Detect the position of The window with Tetris game
windows_list = []
toplist = []
def enum_win(hwnd, result):
    win_text = win32gui.GetWindowText(hwnd)
    windows_list.append((hwnd, win_text))
win32gui.EnumWindows(enum_win, toplist)

# Game handle
game_hwnd = 0
for (hwnd, win_text) in windows_list:
    if win_text.startswith("open-cv-car"):
        print(hwnd, win_text)
        game_hwnd = hwnd
print(game_hwnd)

class SimpleEcho(WebSocket):

    def handleMessage(self):
        print('message', self.data.decode("utf-8"))
        if self.data.decode("utf-8") == 'start':
            def run(*args):

                while True:
                    position = win32gui.GetWindowRect(game_hwnd)


                    # Take screenshot
                    screenshot = ImageGrab.grab(position)
                    screenshot = np.array(screenshot)

                    borderX = borderY = 5
                    startX = 16 
                    startY = 128
                    cameraSizeX = cameraSizeY = 256 

                    screenshot = screenshot[startY + borderY:startY + cameraSizeY - borderY, startX + borderX:startX + cameraSizeX - borderX]

                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)


                    # screenshot = screenshot[startY:startY + borderY * 2 + cameraSizeY, startX:startX + borderX * 2 + cameraSizeX]
                    # bbox, label, conf = cv.detect_common_objects(screenshot, enable_gpu=True)
                    # yolo_screenshot = draw_bbox(screenshot, bbox, label, conf)
                    

                    try:
                        vert_shift, screenshot = lane2.process(screenshot)
                        
                        self.sendMessage(str(vert_shift))
                    except:
                        pass
                        
                    try:
                        classes, confidences, boxes = net.detect(screenshot, confThreshold=0.5)
                        classesFlatten = classes.flatten()
                        # print(classesFlatten, 12 in classesFlatten)

                        if 13 in classesFlatten:
                            print("classes", classes)
                            
                            for classId, confidence, box in zip(classesFlatten, confidences.flatten(), boxes):
                                # print(classId, confidence)
                                cv2.rectangle(screenshot, box, color=(0, 255, 0))
                    except:
                        pass
 
                    cv2.imshow("Screen", screenshot)

                    key = cv2.waitKey(1)
                    if key == 27:
                        break

                cv2.destroyAllWindows()

                # try: 
                #     self.sendMessage(str(lane2.process(img)))
                # except:
                #     pass
            thread.start_new_thread(run, ())
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
        
    def handleClose(self):
        print(self.address, 'closed')

server = SimpleWebSocketServer('localhost', 12345, SimpleEcho)
server.serveforever()
