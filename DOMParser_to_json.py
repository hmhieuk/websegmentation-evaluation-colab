import os
import json
import time
from urllib.parse import urlparse
from datetime import datetime
from selenium import webdriver
from DomNode import DomNode
from DomBlock import DomBlock
from PIL import Image, ImageDraw, ImageFont
import bs4
import cv2

from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
    
from selenium.webdriver import FirefoxOptions

from selenium.webdriver.chrome.service import Service

def findInMappingList(node, mapping):
    for pair in mapping:
        if node in pair:
            return pair

def isIdentical(node1, node2, img1, img2):    
    visual_cues_1 = node1.visual_cues['bounds']
    visual_cues_2 = node2.visual_cues['bounds']

    x1 = int(visual_cues_1['x'])
    y1 = int(visual_cues_1['y'])
    w1 = int(visual_cues_1['width'])
    h1 = int(visual_cues_1['height'])
    x2 = int(visual_cues_2['x'])
    y2 = int(visual_cues_2['y'])
    w2 = int(visual_cues_2['width'])
    h2 = int(visual_cues_2['height'])

    node_image_1 = img1[y1:y1+h1, x1:x1+w1]
    node_image_2 = img2[y2:y2+h2, x2:x2+w2]
    
    hist_img1 = cv2.calcHist([node_image_1], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
    hist_img1[255, 255, 255] = 0
    cv2.normalize(hist_img1, hist_img1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    hist_img2 = cv2.calcHist([node_image_2], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
    hist_img2[255, 255, 255] = 0
    cv2.normalize(hist_img2, hist_img2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    metric_val = cv2.compareHist(hist_img1, hist_img2, cv2.HISTCMP_CORREL)
    return metric_val >= 0.98

def changeClassifier(node, mapping, img1, img2):
    if node is None:
        return

    pair_contains_node = findInMappingList(node, mapping)
    if pair_contains_node is not None:
        mapping.remove(pair_contains_node)
        if None in pair_contains_node:
            if node == pair_contains_node[0]:
                node.setTypeOfChange('deleted')
            else:
                node.setTypeOfChange('added')
        else:
            if node == pair_contains_node[0]:
                node.setMappingNode(pair_contains_node[1])
            else:
                node.setMappingNode(pair_contains_node[0])
            
            if isIdentical(pair_contains_node[0], pair_contains_node[1], img1, img2):
                node.setTypeOfChange('identical')
            else:
                node.setTypeOfChange('modified')

    if node.childNodes:
        for child in node.childNodes:
            changeClassifier(child, mapping, img1, img2)

def drawChangingNode(dr, node, allnodes=False):
    if allnodes == False:
        if node is None:
            return
        if node.isBlockNode or node.isRecordNode:    
            bb = node.visual_cues['bounds']
            color = None
            if node.typeOfChange == 'added':
                color = 'green'
            elif node.typeOfChange == 'deleted':
                color = 'red'
            elif node.typeOfChange == 'identical':
                color = 'violet'
            elif node.typeOfChange == 'modified':
                color = 'yellow'
            else: 
                # color = 'blue'
                return

            cor = (bb['x'], bb['y'], bb['x'] + bb['width'], bb['y'] + bb['height'])
            line = (cor[0], cor[1], cor[0], cor[3])
            dr.line(line, fill=color, width=4)
            line = (cor[0], cor[1], cor[2], cor[1])
            dr.line(line, fill=color, width=4)
            line = (cor[0], cor[3], cor[2], cor[3])
            dr.line(line, fill=color, width=4)
            line = (cor[2], cor[1], cor[2], cor[3])
            dr.line(line, fill=color, width=4)
            font = ImageFont.truetype("JetBrainsMono-Bold.ttf", 16)
            if node.sid is not None: 
                dr.text((bb['x'], bb['y']), node.sid, 'black', font=font)

        if node.childNodes:
            for child in node.childNodes:
                drawChangingNode(dr, child)
    else:
        if node is None:
            return   
        
        bb = node.visual_cues['bounds']
        color = None
        if node.typeOfChange == 'added':
            color = 'green'
        elif node.typeOfChange == 'deleted':
            color = 'red'
        elif node.typeOfChange == 'identical':
            color = 'violet'
        elif node.typeOfChange == 'modified':
            color = 'yellow'
        else: 
            # color = 'blue'
            return

        cor = (bb['x'], bb['y'], bb['x'] + bb['width'], bb['y'] + bb['height'])
        line = (cor[0], cor[1], cor[0], cor[3])
        dr.line(line, fill=color, width=4)
        line = (cor[0], cor[1], cor[2], cor[1])
        dr.line(line, fill=color, width=4)
        line = (cor[0], cor[3], cor[2], cor[3])
        dr.line(line, fill=color, width=4)
        line = (cor[2], cor[1], cor[2], cor[3])
        dr.line(line, fill=color, width=4)

        if node.childNodes:
            for child in node.childNodes:
                drawChangingNode(dr, child)

class DOMParser_to_json:
    def __init__(self, urlStr, grainSegment=False, segmentMinLevel = 0, visual_cues_dict = None, id=None, nodes_dict=None, out_json=None):
        self.url = None
        self.fileName = None
        self.browser = None
        self.domOut = None
        self.imgOut = None
        self.html = None
        self.base_dir = ""
        self.root_node = None
        self.nodeList = []
        self.min_level = segmentMinLevel
        self.visual_cues_dict = visual_cues_dict
        self.nodes_dict = nodes_dict
        self.setUrl(urlStr, id)
        self.setDriver()
        self.getWebPage()
        self.killDriver()
        # self.getScreenshot()
        self.getDomTree(out_json)
        # self.segmentTime = self.segment(grainSegment)

    def getDomFile(self):
        return self.domOut

    def getImgFile(self):
        return self.imgOut

    def setUrl(self, urlStr, id):
        self.url = urlStr

        if urlStr.startswith('file:'):
            filename = urlStr.split('/')[-1]
            name = filename.split('.')[0]
            newpath = r'Snapshots/' + id +name + '_' + \
                str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '/'
            self.fileName = newpath + name
            os.makedirs(newpath)
            self.base_dir = newpath
            return

        if urlStr.startswith('https://') or urlStr.startswith('http://'):
            self.url = urlStr
        else:
            self.url = 'https://' + urlStr
        parse_object = urlparse(self.url)
        newpath = r'Snapshots/' + parse_object.netloc + '_' + str(
            datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '/'
        self.fileName = newpath + parse_object.netloc
        os.makedirs(newpath)
        self.base_dir = newpath

    def setDriver(self):
        opts = FirefoxOptions()
        opts.add_argument("--headless")
        self.browser = webdriver.Firefox(executable_path=
                GeckoDriverManager().install(), options=opts)
        self.browser.implicitly_wait(1000)

    def getWebPage(self):
        print(self.url)
        # input()
        self.browser.get(self.url)

    def killDriver(self):
        self.browser.close()

    @staticmethod
    def toHTMLFile(page_source):
        with open("page_source.html", "w") as file:
            file.write(str(page_source))
        file.close()

    def toDOM(self, obj, parentNode=None, level=0):
        if isinstance(obj, str):
            json_obj = json.loads(obj)
        else:
            json_obj = obj
        nodeType = json_obj['nodeType']
        node = DomNode(nodeType, level)
        if nodeType == 1:  # ELEMENT NODE
            node.createElement(json_obj['tagName'], parentNode)
            attributes = json_obj['attributes']
            if attributes is not None:
                node.setAttributes(attributes)
            visual_cues = json_obj['visual_cues']
            if visual_cues is not None:
                node.setVisual_cues(visual_cues)
            xpath = json_obj['xpath']
            if xpath is not None:
                xpath = normalize_xpath(xpath)
                node.setXpath(xpath)
                if xpath in self.nodes_dict:
                    node.bbox = self.nodes_dict[xpath]
                else:
                    node.bbox = None

        elif nodeType == 3:
            node.createTextNode(json_obj['nodeValue'], parentNode)
            if node.parentNode is not None:
                visual_cues = node.parentNode.visual_cues
                if visual_cues is not None:
                    node.setVisual_cues(visual_cues)
                xpath = node.parentNode.xpath
                if xpath is not None:
                    xpath = normalize_xpath(xpath)
                    node.setXpath(xpath)
                    if xpath in self.nodes_dict:
                        node.bbox = self.nodes_dict[xpath]
                    else:
                        node.bbox = None
                    
        else:
            return node

        self.nodeList.append(node)
        if nodeType == 1:
            childNodes = json_obj['childNodes']
            for i in range(0, len(childNodes)):
                if childNodes[i]:
                    if childNodes[i]['nodeType'] == 1:
                        node.appendChild(self.toDOM(childNodes[i], node, level + 1))
                    if childNodes[i]['nodeType'] == 3:
                        try:
                            if not childNodes[i]['nodeValue'].isspace():
                                node.appendChild(self.toDOM(childNodes[i], node, level + 1))
                        except KeyError:
                            print('abnormal text node')

        return node

    def getDomTree(self, out_json):
        file = open("dom.js", 'r')
        jscript = file.read()
        file.close()

        jscript += '\nreturn JSON.stringify(toJSON(document.getElementsByTagName("BODY")[0], "/HTML[1]", "BODY", 1));'
        x = self.browser.execute_script(jscript)

        # json_object = json.dumps(x, indent=4)
        with open(out_json, "w") as file:
            file.write(x)
        file.close()

        self.root_node = self.toDOM(x)

    def segment(self, grainSegment=False):
        start = time.time()
        self.pruning(self.root_node)
        self.partial_tree_matching(grainSegment)
        self.backtracking()
        self.setIsBlockNode(self.root_node)
        self.output()
        return time.time() - start

    def getScreenshot(self):
        self.default_width = 1366
        self.total_height = self.browser.execute_script(
            "return document.body.parentNode.scrollHeight")
        self.browser.set_window_size(self.default_width, self.total_height)
        time.sleep(5)  # Wait for the page to finish loading
        self.imgOut = self.fileName + '.png'
        self.browser.save_screenshot(self.imgOut)

    def visualize_elements(self, save_image=False, nodes=None, index=[], color=None, extractEach=False):
        if color is None:
            color = ["red"]*len(nodes)

        img = Image.open(self.imgOut)
        dr = ImageDraw.Draw(img)

        visualization_nodes = None
        if nodes is not None:
            visualization_nodes = nodes
        else:
            visualization_nodes = self.nodeList

        for i, node in enumerate(visualization_nodes):
            # Initialize rectangle
            bb = node.visual_cues['bounds']
            cor = (bb['x'], bb['y'], bb['x'] +
                   bb['width'], bb['y'] + bb['height'])
            line = (cor[0], cor[1], cor[0], cor[3])
            dr.line(line, fill=color[i], width=4)
            line = (cor[0], cor[1], cor[2], cor[1])
            dr.line(line, fill=color[i], width=4)
            line = (cor[0], cor[3], cor[2], cor[3])
            dr.line(line, fill=color[i], width=4)
            line = (cor[2], cor[1], cor[2], cor[3])
            dr.line(line, fill=color[i], width=4)

            # Draw index as number
            index_text = str(index[i]) if i < len(index) else str(i)
            # font = ImageFont.truetype('arial.ttf', 30)
            text_width, text_height = dr.textsize(index_text)
            text_pos = (cor[0], cor[1])
            dr.rectangle((text_pos[0], text_pos[1], text_pos[0] +
                         text_width, text_pos[1] + text_height), fill=color[i])
            dr.text(text_pos, index_text, fill="black")

        if save_image:
            imagename = self.imgOut.split('/')[-1]
            filename = imagename.split('.png')[0] + '_viz.png'
            save_path = self.imgOut.split(imagename)[0]+filename

            i = 1
            while os.path.exists(save_path):
                save_path = self.imgOut.split(imagename)[0] + imagename.split('.png')[0] + '_viz' + str(i) + '.png'
                i += 1
            img.save(save_path)

        else:
            img.show()

    def pruning(self, tagbody):
        tagbody.lid = str(-1)
        tagbody.sn = str(1)
        self.allnodes = [tagbody]
        i = 0
        while len(self.allnodes) > i:
            children = []
            for child in self.allnodes[i].childNodes:
                if child.nodeType == 1:
                    children.append(child)
            sn = len(children)

            for child in children:
                child.lid = str(i)
                child.sn = str(sn)
                self.allnodes.append(child)
            i += 1
        pass

    def partial_tree_matching(self, grainSegment=False):
        self.blocks = []

        lid_old = -2

        i = 0
        while i < len(self.allnodes):

            node = self.allnodes[i]

            if node.isExtracted:
                i += 1
                continue
            sn, lid = int(node.sn), int(node.lid)

            if lid != lid_old:
                max_window_size = int(sn / 2)
                lid_old = lid

            for ws in range(1, max_window_size + 1):

                pew, cew, new = [], [], []

                for wi in range(i - ws, i + 2 * ws):

                    if wi >= 0 and wi < len(self.allnodes) and int(self.allnodes[wi].lid) == lid:
                        cnode = self.allnodes[wi]
                        if wi >= i - ws and wi < i:
                            pew.append(cnode)
                        if wi >= i and wi < i + ws:
                            cew.append(cnode)
                        if wi >= i + ws and wi < i + 2 * ws:
                            new.append(cnode)

                        pass

                isle = self.__compare_nodes(pew, cew, grainSegment)
                isre = self.__compare_nodes(cew, new, grainSegment)

                if isle or isre:
                    self.blocks.append(cew)
                    self.markBlockNode(cew)
                    i += ws - 1
                    max_window_size = len(cew)
                    self.__mark_extracted(cew)
                    break
            i += 1
        pass

    def __mark_extracted(self, nodes):
        for node in nodes:
            node.isExtracted = True
            lid = node.lid
            parent = node
            while parent.parentNode is not None:
                parent = parent.parentNode
                parent.isExtracted = True
                parent.sid = lid

            nodecols = [node]
            for nodecol in nodecols:
                for child in nodecol.childNodes:
                    if child.nodeType == 1:
                        nodecols.append(child)
                nodecol.isExtracted = True

    def __compare_nodes(self, nodes1, nodes2, grainSegment=False):
        if len(nodes1) == 0 or len(nodes2) == 0:
            return False

        return self.__get_nodes_children_structure(nodes1, grainSegment) == self.__get_nodes_children_structure(nodes2, grainSegment)

    def __get_nodes_children_structure(self, nodes, grainSegment=False):
        structure = []
        for node in nodes:
            childStruct = self.__get_node_children_structure(node, grainSegment)
            if len(structure) > 0 and structure[-1] == childStruct and not grainSegment:
                continue
            else:
                structure.append(childStruct)
        return structure

    def __get_node_children_structure(self, node, grainSegment=False):
        nodes = [node]
        structure = []
        for node in nodes:
            for child in node.childNodes:
                if child.nodeType == 1:
                    nodes.append(child)
            if len(structure) > 0 and structure[-1] == node.tagName and not grainSegment:
                continue
            else:
                structure.append(node.tagName)
        return structure

    def backtracking(self):
        for node in self.allnodes:
            if (node.tagName != "body") and (node.parentNode is not None) and (not node.isExtracted) and (
                    node.parentNode.isExtracted):
                self.blocks.append([node])
                self.markBlockNode([node])
                self.__mark_extracted([node])

    def setIsBlockNode(self, node):
        if len(node.childNodes) == 0 or node.isBlockNode or node.nodeType == 3:
            return True
        
        all_block_nodes = True
        for child in node.childNodes:
            child_block_node = self.setIsBlockNode(child)
            all_block_nodes = all_block_nodes and child_block_node
        if all_block_nodes:
            node.isBlockNode = True
            self.blocks.append([node])
            self.markBlockNode([node])
            if node.level >= self.min_level:
                for child in node.childNodes:
                    self.setIsNotBlockNode(child)
        return node.isBlockNode
    
    def setIsNotBlockNode(self, node):
        if len(node.childNodes) == 0:
            return node.isBlockNode

        for child in node.childNodes:
            self.setIsNotBlockNode(child)
        node.isBlockNode = False
        return node.isBlockNode

    def output(self):

        segids = []
        segs = dict()
        self.domBlocks = []
        self.blocksNode = []
        for i, block in enumerate(self.blocks):
            domNodeList = block

            lid = block[0].lid

            if lid not in segids:
                segids.append(lid)
            sid = str(segids.index(lid))

            if block[0].parentNode and sid not in segs:
                block[0].parentNode.sid = sid
                segs[sid] = DomBlock(domNodeList, block[0].parentNode, sid)
            
            if block[0].parentNode:
                segs[sid].records.extend(block)
                for node in block:
                    node.isRecordNode = True

        for key, value in segs.items():
            self.domBlocks.append(value)
            value.domNode.isBlockNode = True
            self.blocksNode.append(value.domNode)
        
        # self.setBlockNode(self.root_node)
                
    def setBlockNode(self, node):
        if node in self.blocksNode:
            node.isBlockNode = True
        for child in node.childNodes:
            if child.nodeType == 1:
                self.setBlockNode(child)
        pass

    def markBlockNode(self, nodes):
        for node in nodes:
            node.isBlockNode = True

    def mappingTree(self, mapping, img1, img2):
        changeClassifier(self.root_node, mapping, img1, img2)

    def visualize_changes(self, allnodes=False):
        img = Image.open(self.imgOut)
        draw = ImageDraw.Draw(img)
        drawChangingNode(draw, self.root_node, allnodes)
        img.save(self.base_dir+'visualize_changes.png')


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