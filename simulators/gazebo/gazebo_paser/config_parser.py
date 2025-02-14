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
        return None
    except FileNotFoundError:
        print(f"File couldn't be found : {fp}")
        return None

def print_xml_tree(element, indent=0):
    """Prints an XML element and its children in a tree format."""
    print("  " * indent + "<" + element.tag + ">")
    for child in element:
        print_xml_tree(child, indent + 1)
    if element.text is not None and element.text.strip():
         print("  " * (indent+1) + element.text.strip())
    print("  " * indent + "</" + element.tag + ">")

def main():
    # Requires 2 items <target sdf> and <gazebo_template.json>
    if len(sys.argv) != 3:
        print("Incorrect usage please use python config_parser.py <filename.sdf> <gazebo_template.json>")
        return

    # Loads gazebo template json component
    try:
        with open(sys.argv[2], 'r') as config:
            config_json = json.load(config)
            TRANSMISSION_TYPES = config_json['actuator']
            SENSING_TYPES = config_json['sensor']

    except FileNotFoundError as e:
        print(f"Couldn't open the gazebo config template <" + sys.argv[2] + ">\n{e}")
        quit()

    # Imports the sdf file as an xml structure to navigate through
    xml_tree = sdf_to_xml(sys.argv[1])

    # Prints out the elements in the tree
    root = xml_tree.getroot()
    print_xml_tree(root)

    print("\n~Opened all files successfully~\n")
    
    return

if __name__ =="__main__":
    main()



