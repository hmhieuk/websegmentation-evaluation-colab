# read json 000000/ground-truth.json

import csv
import datetime
import json
import os
import threading

import cv2

from DOMParser_to_json import DOMParser_to_json


class Annotations:
    def __init__(self, id, height, width, segmentations, algorithm):
        self.id = id
        self.height = height
        self.width = width
        self.segmentations = segmentations
        self.algorithm = algorithm

    def append_segmentation(self, segmentation):
        self.segmentations.append([[segmentation]])

    def to_dict(self):
        segmentations = {}
        segmentations[self.algorithm] = self.segmentations

        return {
            "id": self.id,
            "height": self.height,
            "width": self.width,
            "segmentations": segmentations
        }

    def to_json(self):
        return json.dumps(self.to_dict())


def get_width_height_from_ground_truth(ground_truth_file):
    with open(ground_truth_file, "r") as f:
        ground_truth = json.load(f)
        return ground_truth["width"], ground_truth["height"]


def segment_dom(id, domfile, output_file, log_file, nodes_file, ground_truth_file, out_json):
    domfile = "file://" + domfile
    coordinates = nodes_file_to_json(nodes_file)

    dom_document_1 = DOMParser_to_json(
        domfile, grainSegment=False, segmentMinLevel=0, id=id, nodes_dict=coordinates, out_json=out_json)


def nodes_file_to_json(nodes_file):
    with open(nodes_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        coordinates = {}
        for row in reader:
            xpath = row['xpath']
            left = int(row['left'])
            bottom = int(row['bottom'])
            right = int(row['right'])
            top = int(row['top'])
            coordinates[xpath] = {'x': left, 'y': top,
                                  'width': right - left, 'height': bottom - top}
        return coordinates


def normalize_xpath(xpath):
    tags = xpath.split("/")[1:]
    for i, tag in enumerate(tags):
        if "[" in tag:
            tag_name, index = tag.split("[")
            tags[i] = tag_name.upper() + "[" + index
        else:
            tags[i] = tag.upper() + "[1]"
    result = "/" + "/".join(tags)
    return result


def segment_file(id, dataset_path, common_log_file):
    domfile = os.path.join(dataset_path, id, "dom.html")
    output_file = os.path.join(dataset_path, id, "annotations.json")
    log_file = os.path.join(dataset_path, id, "log.txt")
    nodes_file = os.path.join(dataset_path, id, "nodes.csv")
    ground_truth_file = os.path.join(dataset_path, id, "ground-truth.json")
    out_json = os.path.join(dataset_path, id, "dom.json")
    segment_dom(
        id, domfile, output_file, log_file, nodes_file, ground_truth_file, out_json)


def main():
    dataset_path = "/content/drive/MyDrive/dataset-websis/webis-webseg-20"
    folder_names = os.listdir(dataset_path)
    folder_names.sort()
    # ignore .DS_Store,
    folder_names = [
        folder_name for folder_name in folder_names if folder_name[0] != "."]
    threads = []
    batch_size = 10
    for i in range(0, len(folder_names), batch_size):
        print("processing batch " + str(i))
        batch = folder_names[i:i+batch_size]
        for url in batch:
            t = threading.Thread(target=segment_file,
                                 args=(url, dataset_path, log_file))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        input("Press Enter to continue...")


if __name__ == "__main__":
    main()
