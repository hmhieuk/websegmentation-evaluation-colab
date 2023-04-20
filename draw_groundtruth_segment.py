#read json 000000/ground-truth.json

import json
import os

import cv2

#get the list of all folder in the dataset

# folder_names = os.listdir(".")
# for folder_name in folder_names:
folder_name = "000000"
json_file = f"{folder_name}/ground-truth.json"
screenshot_file = f"{folder_name}/screenshot.png"
#check if 2 files exist
if not os.path.exists(json_file) or not os.path.exists(screenshot_file):
    print(f"{folder_name} does not exist")
    # continue

with open(json_file, "r") as f:
    json_data = json.load(f)

segments = json_data["segmentations"]["majority-vote"]
# each segment is a list of vertices, each vertex is a list of 2 numbers. The first vertex is the same as the last vertex
# draw the segment on the image
image = cv2.imread("000000/screenshot.png")

count = 0
for listSeg in segments:
    for segment in listSeg:
        for s in segment:
            count += 1
            print(count)
            for i in range(len(s) - 1):
                cv2.line(image, (s[i][0], s[i][1]), (s[i+1][0], s[i+1][1]), (0, 0, 255), 2)

    cv2.imwrite("000000/ground-truth.png", image)




