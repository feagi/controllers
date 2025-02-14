import json
import sys
import os
import xml.etree.ElementTree as ET

def sdf_to_xml(fp):
    try:
        tree = ET.parse(fp)
        return tree
    except ET.ParseError as e:
        print(f"Couldn't parse SDF file\n{e}")

def print_element_info(element, indent=""):
    print(f"{indent}<{element.tag}>")
    if element.text and element.text.strip():
        print(f"{indent}  {element.text.strip()}")
    for subelement in element:
        print_element_info(subelement, indent + "  ")
        print(f"{indent}</{element.tag}>")

def process_xml_tree(xml_tree):
    if xml_tree is not None:
        root = xml_tree.getroot()
        print_element_info(root)

def main():
    if len(sys.argv) != 3:
        print("Incorrect usage please use python config_parser.py <filename.sdf> <gazebo_template.json>")
        return

    #begin opening files
    try:
        with open(sys.argv[2], 'r') as config:
            config_json = json.load(config)

    except FileNotFoundError as e:
        print(f"Couldn't open the gazebo config template <" + sys.argv[2] + ">\n{e}")
        quit()

    try:
        with open(sys.argv[1], 'r') as sdf:
            sdf_file = sdf.read()
            
    except FileNotFoundError as e:
        print(f"Couldn't open the target sdf file <" + sys.argv[1] + ">\n{e}");
        quit()
    
    #print(config_json)
    process_xml_tree(sdf_to_xml(sys.argv[2]))
    #print(sdf_file)
    return

if __name__ =="__main__":
    main()



