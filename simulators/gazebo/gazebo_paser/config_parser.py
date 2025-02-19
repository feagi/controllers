import json
import sys
import os
import xml.etree.ElementTree as ET

# Description : used to parse the SDF to an XML structure which can be iterated through
# INPUT : file path (String)
# Output on success : XML tree
# Output on fail : None
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

# Description : used to strip the XML tree of any unnecessary elements
# INPUT : tree element (expected to be the root)
# Output on success : XML tree
# Output on fail : None
def strip_tree (element, found_elements): 
    for child in element:
        #print(element.tag)
        if element.tag in ALLOW_LIST:
            found_elements.append(element)
        else:
            strip_tree(child, found_elements)
            

# !Ignore this, it's unimportant and was just used for testing! #
def explore_tree(element):
    tags = []
    for child in element:
        if element.tag not in tags:
            tags.append(element.tag)
        explore_tree(child)

    return tags
        #if child.text is not None and element.text.strip():



def main():
    global TRANSMISSION_TYPES
    global SENSING_TYPES
    global ALLOW_LIST 
    global IGNORE_LIST 
    
    # Requires 2 items <target sdf> and <gazebo_template.json>
    if len(sys.argv) != 3:
        print("Incorrect usage please use python config_parser.py <filename.sdf> <gazebo_template.json>")
        return

    # Loads gazebo template json component
    try:
        with open(sys.argv[2], 'r') as config:
            config_json = json.load(config)

        try:
            TRANSMISSION_TYPES = config_json['actuator']
            SENSING_TYPES = config_json['sensor']
            ALLOW_LIST = config_json['allow_list']
            IGNORE_LIST = config_json['ignore_list']

        except KeyError as err :
            print(f"Gazebo config seems invalid : \n{err}")

    except FileNotFoundError as err:
        print(f"Couldn't open the gazebo config template <" + sys.argv[2] + ">\n{err}")
        quit()

    print("\n~Opened all files successfully~\n")
    
    # Imports the sdf file as an xml structure to navigate through
    xml_tree = sdf_to_xml(sys.argv[1])

    # Prints out the elements in the tree
    root = xml_tree.getroot()

    # Will store all found elements
    found_elements = []

    # Grabs all allowed sdf elements (elements matching those in gazebo_config['allow_list'])
    strip_tree(root, found_elements)

    # At this point we found all elements we're looking for, now we begin parsing it into terms feagi can understand
    print(found_elements)

    
    return

if __name__ =="__main__":
    main()



