#!/usr/bin/ python3

import hashlib
import os, sys
import json
import logging
import tempfile
import optparse
import subprocess
import datetime, time
import threading, multiprocessing
from xml.dom.minidom import parse
import xml.dom.minidom

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))

class operator() :
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.tree = xml.dom.minidom.parse(self.xml_file)
        self.root_node = self.tree .documentElement

    def new_node(self, name, attribute_dict, text, child_node_list):
        node = self.tree.createElement(name)
        for attr_index in attribute_dict:
            node.setAttribute(attr_index, attribute_dict[attr_index])
        if text != '':
            node.appendChild(self.treetree.createTextNode(text))
        for child_index in child_node_list:
            node.appendChild(child_index)
        return node

    def get_node_by_name(self, farther_node, node_name) :
        list_temp= farther_node.getElementsByTagName(node_name)
        same_level_list=[]
        for index in list_temp:
            if index.parentNode == farther_node:
                same_level_list.append(index)
        return same_level_list

    def get_text_by_node(self, node) :
        for index in node.childNodes:
            #print ('[%s] type[%d]'%(index, index. nodeType))
            if index.nodeType == 3:
                text_origin = index.data
                if text_origin.replace('\n','').replace('\r','').replace('\t','').replace(' ','') == '':
                    return ''
                return text_origin
        return ''

    def get_child_namelist(self, farther_node) :
        namelist = []
        node = farther_node.childNodes
        for i in range (node.length):
            if node[i].nodeType == 1:
                name = node[i].nodeName
                if namelist.count(name) == 0:
                    name_list.append(node[i].nodeName)
        return namelist

    def walk_node (self, farther_node) :
        dict = {}
        child_list = self.get_child_namelist(farther_node)
        for child_index in child_list:
            index_node_list = self.get_node_by_name(farther_node, child_index)
            for node_index in index_node_list:
                child_name = child_index
                if node_index.hasAttributes():              #parse all attributes
                    for attr_index in node_index.attributes.keys():
                        child_name = child_name + ' ' + attr_index + '=' + node_index.getAttribute(attr_index)
                index_data = self.get_text_by_node(node_index)
                if node_index.nodeType != 1 or index_data == '':
                    index_data = self.walk_node(node_index) #go deeper if node is a element, or a text
                if len(index_node_list) > 1:                #if have multi same name lable. make it a list
                    temp_list = dict.get(child_name, [])    #if cannot find the name, new a list
                    temp_list.append(index_data)
                    dict.update({child_name: temp_list})
                else:
                    dict.update({child_name: index_data})
        return dict

