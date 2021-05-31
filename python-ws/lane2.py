import matplotlib.pylab as plt
import cv2
import numpy as np
import warnings

day_canny = (50, 80)
night_canny = (10, 40)

def make_coordinate(img, line_param):
    slope, intercept = line_param
    y1 = img.shape[0]
    y2 = int(y1 * (3 / 5))
    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)
    return np.array([x1, y1, x2, y2])

def average_slope_intercept(img, lines):
    left_fit, right_fit = [], []
    
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        params = np.polyfit((x1, x2), (y1, y2), 1)
        slope = params[0]
        intercept = params[1]
        if slope < 0:
            left_fit.append((slope, intercept))
        else:
            right_fit.append((slope, intercept))
    left_fit_avg = np.average(left_fit, axis=0)
    right_fit_avg = np.average(right_fit, axis=0)
    left_line = make_coordinate(img, left_fit_avg)
    right_line = make_coordinate(img, right_fit_avg)
    return np.array([left_line, right_line])


def region_of_interest(img, vertices):
    mask = np.zeros_like(img)
    #channel_count = img.shape[2]
    match_mask_color = 255
    cv2.fillPoly(mask, vertices, match_mask_color)
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

def draw_lines(img, lines):
    img = np.copy(img)
    blank_image = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)

    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(blank_image, (x1,y1), (x2,y2), (0, 255, 0), thickness=10)

    img = cv2.addWeighted(img, 0.8, blank_image, 1, 0.0)
    return img

def middle_line(lines, height=0.5):
    pointX1 = lines[0][0][0] + (lines[0][0][2] - lines[0][0][0]) * height
    pointX2 = lines[1][0][0] + (lines[1][0][2] - lines[1][0][0]) * height
    pointY1 = lines[0][0][1] + (lines[0][0][3] - lines[0][0][1]) * height
    pointY2 = lines[1][0][1] + (lines[1][0][3] - lines[1][0][1]) * height

    vert_shift = (pointX1 + (pointX2 - pointX1) / 2)
    new_line = [ np.array([int(pointX1), int(pointY1), int(pointX2), int(pointY2)]) ]

    return (vert_shift, new_line)


# = cv2.imread('road.jpg')
#image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
def process(image, roi_height=0.5, is_night_conditions=True):
    # print(image.shape)
    height = image.shape[0]
    width = image.shape[1]
    region_of_interest_vertices = [
        (0, height),
    #    (0, height * roi_height),
    #    (width, height * roi_height),
        (width/4, height*roi_height),
        (3*width/4, height*roi_height),
        (width, height)
    ]
    kernel = np.ones((5, 5), np.float32) / (80 if is_night_conditions else 25)
    smoothed = cv2.filter2D(image, -1, kernel)

    gray_image = cv2.cvtColor(smoothed, cv2.COLOR_RGB2GRAY)
    canny_image = cv2.Canny(gray_image, *(night_canny if is_night_conditions else day_canny))

    cropped_image = region_of_interest(canny_image,
                             np.array([region_of_interest_vertices], np.int32),)
    # cv2.imshow('canny', cropped_image)
    lines = cv2.HoughLinesP(cropped_image,
                            rho=2,
                            theta=np.pi/180,
                            threshold=50,
                            lines=np.array([]),
                            minLineLength=10,
                            maxLineGap=100)

    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            lines = list(map(lambda x: [x], average_slope_intercept(image, lines)))
        except np.RankWarning:
            pass
    
    middle = middle_line(lines, 0.7)
    # print('middle', middle)
    lines.append(middle[1])
    # print(lines)
    # vert_shift = (lines[0][0][0] + (lines[1][0][0] - lines[0][0][0]) / 2) / width
    vert_shift = middle[0] / width
    # print(vert_shift)
    # return vert_shift 
    image_with_lines = draw_lines(image, lines)

    return (vert_shift, image_with_lines, cropped_image)

if __name__ == '__main__':
    # cap = cv2.VideoCapture('test.mp4')
    frame = cv2.imread('file.png')

    # while cap.isOpened():
    # ret, frame = cap.read()
    frame = process(frame)
    while True:
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == 27:
            break

    # cap.release()
    cv2.destroyAllWindows()
