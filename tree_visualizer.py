import threading
import numpy as np
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import networkx as nx

import json
from DOMParser import DOMParser


def dom_tree_to_networkx(root):
    G = nx.DiGraph()
    _traverse_dom_tree(root, G)
    return G


def _traverse_dom_tree(node, G):
    for child in node.childNodes:
        G.add_edge(node, child)
        _traverse_dom_tree(child, G)


# from bs4 import BeautifulSoup


def plot_2_tree_structure(G1, G2, connections=[], fileName=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    # pos = nx.spring_layout(G)
    options1 = {
        'node_size': 100,
        'width': 3,
        'arrowstyle': '-|>',
        'arrowsize': 10,
        'node_color': 'white',
    }

    options2 = {
        'node_color': 'white',
        'node_size': 100,
        'width': 3,
        'arrowstyle': '-|>',
        'arrowsize': 10,
    }

    pos1 = nx.nx_agraph.graphviz_layout(G1, prog="dot")
    pos2 = nx.nx_agraph.graphviz_layout(G2, prog="dot")
    pos2_shifted = {k: (v[0] + 1000, v[1]-500) for k, v in pos2.items()}
    pos_combined = {**pos1, **pos2_shifted}

    # if node.tagName == None: node.tagName = Node.text  else: node.tagName = node.tagName
    labels1 = {}
    for node in G1.nodes():
        if node.tagName is None:
            labels1[node] = node.visual_cues["text"]
        else:
            labels1[node] = node.tagName

    labels2 = {}
    for node in G2.nodes():
        if node.tagName is None:
            labels2[node] = node.visual_cues["text"]
        else:
            labels2[node] = node.tagName

    nx.draw_networkx(G1, pos1, arrows=True, **options1, ax=ax,
                     font_size=7, with_labels=True, labels=labels1)
    nx.draw_networkx(G2, pos2_shifted, arrows=True, **options2,
                     ax=ax, font_size=7, with_labels=True, labels=labels2)

    # Draw dashed lines between corresponding nodes
    for node1, node2 in connections:
        if node1 is None or node2 is None:
            continue
        pos1_node = pos_combined[node1]
        pos2_node = pos_combined[node2]
        x = [pos1_node[0], pos2_node[0]]
        y = [pos1_node[1], pos2_node[1]]
        random_color = np.random.rand(3,)
        ax.plot(x, y, linestyle='--', color='red', linewidth=1, alpha=0.5)

    plt.savefig(fileName, dpi=150, bbox_inches='tight', pad_inches=1)
    plt.show()


def plot_tree_structure(G, fileName=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    color_map = []
    for node in G:
        if node.isBlockNode:
            # input("Is block node: " + node.tagName)
            color_map.append('green')
        elif node.isRecordNode:
            color_map.append('blue')
        else:
            color_map.append('red')

    # pos = nx.spring_layout(G)
    options = {
        'node_color': color_map,
        'node_size': 100,
        'width': 3,
        'arrowstyle': '-|>',
        'arrowsize': 20,
    }

    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    # if node.tagName == None: node.tagName = Node.text  else: node.tagName = node.tagName
    labels = {}
    for node in G.nodes():
        if node.tagName is None:
            labels[node] = ""
        else:
            labels[node] = node.tagName

        if node.isBlockNode:
            labels[node] = node.tagName

    nx.draw_networkx(G, pos, arrows=True, **options, ax=ax,
                     font_size=7, with_labels=True, labels=labels)

    # plt.savefig(fileName, dpi=150, bbox_inches='tight', pad_inches=1)
    plt.show()


def main(webpage_1):

    dom_document_1 = DOMParser(webpage_1, grainSegment=False, segmentMinLevel=0)

    dom1 = dom_document_1.root_node

    dom_doc_1, dom_img_1 = dom_document_1.getDomFile(), dom_document_1.getImgFile()

    # create log file
    with open(dom_document_1.base_dir + "/log.txt", "a") as f:
        f.write("Segment time: " + str(dom_document_1.segmentTime) + "\n")
    # digraph1 = dom_tree_to_networkx(dom1)
    # plot_tree_structure(digraph1, fileName="dom1.png")
    visNodes = [node.domNode for node in dom_document_1.domBlocks if node.domNode.visual_cues["visibility"]
                == "visible" and node.domNode.visual_cues["display"] != "none"]
    # dom_document_1.visualize_elements(save_image=True, nodes=visNodes, color=['green'] *len(visNodes))

    # max_depth = [max([node.level for node in visNodes])]
    # print(max_depth)

    # for i in range(1, max_depth[0]):
    #     nodes = [node for node in visNodes if node.level <= i]
    #     dom_document_1.visualize_elements(
    #         save_image=True, nodes=nodes, color=['red'] * len(nodes))
    #     print("Level: ", i, " Number of nodes: ", len(nodes))
    #     # write to log file
    #     with open(dom_document_1.base_dir + "/log.txt", "a") as f:
    #         f.write("Level: " + str(i) + " Number of nodes: " +
    #                 str(len(nodes)) + "\n")

    records = []
    for node in dom_document_1.domBlocks:
        records.extend(node.records)

    with open(dom_document_1.base_dir + "/log.txt", "a") as f:
        f.write("Level: " + str(i) + " Number of records: " +
                    str(len(records)) + "\n")

    dom_document_1.visualize_elements(
        save_image=True, nodes=records, color=['blue'] * len(records))


if __name__ == "__main__":
    # # create new thread to run the main function
    # # read urls from txt file
    # with open("urls.txt", "r") as f:
    #     urls = f.readlines()
    # threads = []
    # #each batch of 10 urls will be run in a separate thread
    # for i in range(0, len(urls), 10):
    #     batch = urls[i:i+10]
    #     for url in batch:
    #         t = threading.Thread(target=main, args=(url,))
    #         threads.append(t)
    #         t.start()
    #     for t in threads:
    #         t.join()
    localURL = "file:////Users/hieu.huynh/Downloads/webis-webseg-20-000000/000000/dom.html"
    # main("https://stackoverflow.com/questions")
    main(localURL)
