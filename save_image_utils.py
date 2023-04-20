from PIL import Image, ImageDraw
import os
from DOMParser import DOMParser
from DomNode import DomNode
import numpy as np

def save_dom_comparison(dom1: DomNode, dom2: DomNode, img1, img2, path1, path2):
    folders = ['modified', 'added', 'deleted', 'identical']
    for folder in folders:
        if not os.path.exists(path1 + folder):
            os.makedirs(path1 + folder)
        if not os.path.exists(path2 + folder):
            os.makedirs(path2 + folder)

    __save_dom_comparison(dom1, img1, img2, 0, path1)
    __save_dom_comparison(dom2, img1, img2, 0, path2)

def __save_dom_comparison(node, img1, img2, id, path):
    if node:
        if node.typeOfChange == 'modified':
            save_image_comparison(node, node.mappingNode,
                                  img1, img2, path +'/modified/' + str(id) + '.png')
        elif node.typeOfChange == 'added':
            save_image_comparison(node, node.mappingNode,
                                  img1, img2, path + '/added/' + str(id) + '.png')
        elif node.typeOfChange == 'deleted':
            save_image_comparison(node, node.mappingNode,
                                  img1, img2, path + '/deleted/' + str(id) + '.png')
        elif node.typeOfChange == 'identical':
            save_image_comparison(node, node.mappingNode,
                                  img1, img2, path + '/identical/' + str(id) + '.png')

    for child in node.childNodes:
        __save_dom_comparison(child, img1, img2, id+1, path)


def save_image_comparison(node1: DomNode, node2: DomNode, img1: np.ndarray, img2:np.ndarray, name):
    img1 = Image.fromarray(img1)
    img2 = Image.fromarray(img2)

    if node1 and node1.visual_cues:
        bb1 = node1.visual_cues['bounds']
        cor1 = (bb1['x'], bb1['y'], bb1['x'] +
                bb1['width'], bb1['y'] + bb1['height'])
    else:
        cor1 = (0, 0, 0, 0)
    
    if node2 and node2.visual_cues:
        bb2 = node2.visual_cues['bounds']
        cor2 = (bb2['x'], bb2['y'], bb2['x'] +
                bb2['width'], bb2['y'] + bb2['height'])
    else:
        cor2 = (0, 0, 0, 0)

    crop1 = img1.crop(cor1)
    crop2 = img2.crop(cor2)

    collage2images(crop1, crop2, name)


def collage2images(img1, img2, name):
    # Define the width of the black line
    line_width = 10

    width = img1.width + img2.width + line_width
    height = max(img1.height, img2.height)

    new_img = Image.new('RGB', (width, height))

    new_img.paste(img1, (0, 0))

    new_img.paste(img2, (img1.width + line_width, 0))
    draw = ImageDraw.Draw(new_img)
    draw.rectangle((img1.width, 0, img1.width +
                   line_width, height), fill='black')
    try:
        new_img.save(name)
    except:
        print('Error saving image: ' + name)
