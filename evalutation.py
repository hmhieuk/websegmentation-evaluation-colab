# read json 000000/ground-truth.json

import csv
import datetime
import json
import os
import threading

import cv2

from DOMParser import DOMParser


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


def segment_dom(id, domfile, output_file, log_file, nodes_file, ground_truth_file):
    domfile = "file://" + domfile
    coordinates = nodes_file_to_json(nodes_file)

    dom_document_1 = DOMParser(
        domfile, grainSegment=False, segmentMinLevel=0, id=id, nodes_dict=coordinates)
    width, height = get_width_height_from_ground_truth(ground_truth_file)
    annotations = Annotations(
        id, height, width, [], "my_algorithm")


    with open(log_file, "a") as f:
        f.write("Segment time: " + str(dom_document_1.segmentTime) + "\n")

    visNodes = [node.domNode for node in dom_document_1.domBlocks if node.domNode.visual_cues["visibility"]
                == "visible" and node.domNode.visual_cues["display"] != "none"]
    filteredNodes = []
    found, not_found = 0, 0
    for node in visNodes:
        bb1 = node.bbox
        print(node.xpath, node.nodeName)
        if bb1 is None:
            not_found += 1
            continue
        found += 1
        cor1 = (bb1['x'], bb1['y'], bb1['x'] +
                bb1['width'], bb1['y'] + bb1['height'])

        cor1 = (int(max(0, cor1[0])), int(max(0, cor1[1])), int(
            min(width, cor1[2])), int(min(height, cor1[3])))

        area = (cor1[2] - cor1[0]) * (cor1[3] - cor1[1])
        ratio = area / (height *
                        width)
        if ratio > 0.7:
            continue

        filteredNodes.append(node)

        segmentation = []
        segmentation.append([cor1[0], cor1[1]])
        segmentation.append([cor1[2], cor1[1]])
        segmentation.append([cor1[2], cor1[3]])
        segmentation.append([cor1[0], cor1[3]])
        segmentation.append([cor1[0], cor1[1]])

        annotations.append_segmentation(segmentation)

    with open(output_file, "w") as f:
        f.write(annotations.to_json())
    return found, not_found


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

    found, notfound = segment_dom(
        id, domfile, output_file, log_file, nodes_file, ground_truth_file)

    with open(common_log_file, "a") as f:
        f.write("ID: " + id)
        f.write(". Found: " + str(found))
        f.write(". Not found: " + str(notfound)+"\n")


def main():
    dataset_path = "/Users/hieu.huynh/Downloads/webis-webseg-20 2"
    random_ids_file = "random_id.json"
    log_file = "log" + str(datetime.datetime.now()) + ".txt"
    with open(random_ids_file, "r") as f:
        random_ids = json.load(f)

    folder_names = random_ids
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
