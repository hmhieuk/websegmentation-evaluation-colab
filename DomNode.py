class DomNode:
    __slots__ = (
        'nodeType',
        'tagName', 
        'nodeName', 
        'nodeValue', 
        'visual_cues', 
        'attributes', 
        'childNodes',
        'parentNode',
        'typeOfChange',
        'mappingNode',
        'lid',
        'sn',
        'isExtracted',
        'sid',
        'isBlockNode',
        'level',
        'isRecordNode',
        'xpath',
        'bbox')
    
    def __init__(self, nodeType, level=None):
        self.parentNode = None
        self.nodeValue = None
        self.tagName = None
        self.nodeName = None
        self.nodeType = nodeType
        self.attributes = dict()
        self.childNodes = []
        self.visual_cues = dict()
        self.bbox = None
        self.typeOfChange = None
        self.lid = None
        self.sn = None
        self.isExtracted = False
        self.sid = None
        self.isBlockNode = False
        self.isRecordNode = False
        self.level = level
        self.mappingNode = None
        self.xpath = None

        
    def createElement(self, tagName, parentNode):
        self.nodeName = tagName
        self.tagName = tagName
        self.parentNode = parentNode
             
    def createTextNode(self, nodeValue, parentNode):
        self.nodeName = '#text'
        self.nodeValue = nodeValue
        self.parentNode = parentNode
        
    def createComment(self, nodeValue, parentNode):
        self.nodeName = "#comment"
        self.nodeValue = nodeValue
        self.parentNode = parentNode
    
    def setAttributes(self, attribute):
        self.attributes = attribute
    
    def setVisual_cues(self, visual_cues):
        self.visual_cues = visual_cues
    
    def appendChild(self, childNode):
        self.childNodes.append(childNode)

    def setIsBlockNode(self, isBlockNode):
        self.isBlockNode = isBlockNode
    
    def setTypeOfChange(self, type_of_change):
        self.typeOfChange = type_of_change
    
    def setMappingNode(self, mapping_node):
        self.mappingNode = mapping_node
    
    def setLevel(self, level):
        self.level = level

    def setXpath(self, xpath):
        self.xpath = xpath