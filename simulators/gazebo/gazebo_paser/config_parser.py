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
        if element.tag in g_config['allow_list']:
            found_elements.append(element)
        else:
            strip_tree(child, found_elements)
            
# Description : used to load all 3 necessary files (feagi template config, gazebo template config, and the target sdf file) 
# INPUT : gazebo config file path, feagi config file path, target sdf file path, array to store found elements in
# Output on success : Populates found_elements with all allowed elements from the sdf
# Output on fail : None
def open_files(gazebo_config_template, feagi_config_template, target_sdf, found_elements):
    global g_config
    global f_config

    try:
        with open(gazebo_config_template, 'r') as config:
            g_config = json.load(config)

    except FileNotFoundError as err:
        print(f"Couldn't open the gazebo config template <" + gazebo_config_template + ">\n{err}")
        quit()

    try:
        with open(feagi_config_template, 'r') as config:
            f_config = json.load(config)
    except FileNotFoundError as err:
        print(f"Couldn't open the feagi config template <" + feagi_config_template + ">\n{err}")

    print("Opened all files successfully...")

    tree = sdf_to_xml(target_sdf)
    root = tree.getroot()
    strip_tree(root, found_elements)

def main():
    # CMD LINE USAGE :
    # 1 - python config_parser.py <target.sdf> 
    #
    #       * Uses default gazebo config : 'gazebo_config_template.json'
    #       * Uses default feagi config : 'feagi_config_template.json'
    #
    # 2 - python config_parser.py <target.sdf> <gazebo_config.json> <feagi_config.json> 
    #
    #   * Both <gazebo_config.json> and <feagi_config.json> or the default files must be in the current directory to work properly *

    # Will store all found elements
    found_elements = []

    num_args = len(sys.argv) - 1

    if num_args == 1:
        print(sys.argv[1] + '\n')
        open_files('gazebo_config_template.json', 'feagi_config_template.json', sys.argv[1], found_elements)
    elif num_args == 3:
        open_files(sys.argv[2], sys.argv[3], sys.argv[1], found_elements)
    else :
        print("Incorrect command usage, please use either :\npython config_parser.py <target.sdf> <gazebo_config.json> <feagi_config.json>\npython config_parser.py <target.sdf>")
        return
    
    print(found_elements)
    return

if __name__ =="__main__":
    main()



