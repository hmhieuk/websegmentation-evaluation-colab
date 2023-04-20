function toJSON(node, parentPath, nodeName, nodeNameNumber) {
  const nodePath = parentPath + "/" + nodeName + "[" + nodeNameNumber + "]";
  node = node || this;
  var obj = {
    nodeType: node.nodeType,
  };
  if (node.tagName) {
    obj.tagName = node.tagName.toLowerCase();
  } else if (node.nodeName) {
    obj.nodeName = node.nodeName;
  }
  if (node.nodeValue) {
    obj.nodeValue = node.nodeValue;
  }
  if (node.nodeType == 1) {
    obj.visual_cues = getCSS(node);
  }

  obj.xpath = nodePath;

  var attrs = node.attributes;
  if (attrs) {
    var length = attrs.length;
    var arr = obj.attributes = {};
    for (var i = 0; i < length; i++) {
      attr_node = attrs.item(i);
      arr[attr_node.nodeName] = attr_node.nodeValue;
    }
  }
  var childNodes = node.childNodes;
  if (childNodes) {
    const counts = {};
    length = childNodes.length;
    arr = obj.childNodes = new Array(length);
    for (i = 0; i < length; i++) {
      const child = childNodes[i];
      if (isVisible(child) && child.tagName != "script") {
        var childName;
        if (child.nodeType == Node.TEXT_NODE) {
          childName = "text()";
        } else {
          childName = child.tagName;
        }

        if (typeof counts[childName] == "undefined") {
          counts[childName] = 1;
        } else {
          counts[childName] += 1;
        }
        arr[i] = toJSON(child, nodePath, childName, counts[childName]);
      }
    }
  }
  return obj;
}

function getCSS(node) {
  var visual_cues = {};
  style = window.getComputedStyle(node);
  visual_cues["bounds"] = node.getBoundingClientRect();
  visual_cues["font-size"] = style.getPropertyValue("font-size");
  visual_cues["font-weight"] = style.getPropertyValue("font-weight");
  visual_cues["background-color"] = style.getPropertyValue("background-color");
  visual_cues["display"] = style.getPropertyValue("display");
  visual_cues["visibility"] = style.getPropertyValue("visibility");
  visual_cues["text"] = node.innerText;
  visual_cues["className"] = node.className;
  return visual_cues;
}

function getXPath(elm) {
  var allNodes = document.getElementsByTagName("*");
  for (var segs = []; elm && elm.nodeType == 1; elm = elm.parentNode) {
    if (elm.hasAttribute("id")) {
      var uniqueIdCount = 0;
      for (var n = 0; n < allNodes.length; n++) {
        if (allNodes[n].hasAttribute("id") && allNodes[n].id == elm.id)
          uniqueIdCount++;
        if (uniqueIdCount > 1) break;
      }
    } else {
      for (i = 1, sib = elm.previousSibling; sib; sib = sib.previousSibling) {
        if (sib.localName == elm.localName) i++;
      }
      segs.unshift(elm.localName.toLowerCase() + "[" + i + "]");
    }
  }
  return segs.length ? "/" + segs.join("/") : null;
}

function toDOM(obj) {
  if (typeof obj == "string") {
    obj = JSON.parse(obj);
  }
  var node,
    nodeType = obj.nodeType;
  switch (nodeType) {
    case 1: //ELEMENT_NODE
      node = document.createElement(obj.tagName);
      var attributes = obj.attributes || [];
      for (var i = 0, len = attributes.length; i < len; i++) {
        var attr = attributes[i];
        node.setAttribute(attr[0], attr[1]);
      }
      break;
    case 3: //TEXT_NODE
      node = document.createTextNode(obj.nodeValue);
      break;
    case 8: //COMMENT_NODE
      node = document.createComment(obj.nodeValue);
      break;
    case 9: //DOCUMENT_NODE
      node = document.implementation.createDocument();
      break;
    case 10: //DOCUMENT_TYPE_NODE
      node = document.implementation.createDocumentType(obj.nodeName);
      break;
    case 11: //DOCUMENT_FRAGMENT_NODE
      node = document.createDocumentFragment();
      break;
    default:
      return node;
  }
  if (nodeType == 1 || nodeType == 11) {
    var childNodes = obj.childNodes || [];
    for (i = 0, len = childNodes.length; i < len; i++) {
      node.appendChild(toDOM(childNodes[i]));
    }
  }
  return node;
}

function isVisible(node) {
  if (node.nodeType == Node.TEXT_NODE) {
    return node.textContent.trim() != "";
  } else if (node.nodeType == Node.ELEMENT_NODE) {
    return !!(
      node.offsetWidth ||
      node.offsetHeight ||
      node.getClientRects().length
    );
  } else {
    return false;
  }
}