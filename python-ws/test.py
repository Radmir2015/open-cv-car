import applescript
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)

def find_bbox_by_window_title(title="Unity"):
    options = kCGWindowListOptionOnScreenOnly
    windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)

    windows = []

    for window in windowList:
        ownerName = window['kCGWindowOwnerName']
        geometry = window['kCGWindowBounds']
        windows.append((ownerName, geometry))

        if (ownerName == title):
            break

    return windows[-1][0] == title and windows[-1][1]

print(find_bbox_by_window_title())