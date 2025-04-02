import json
import sys
import os
import math
from lxml import etree as ET

# CMD LINE USAGE :
# 1 - python config_parser.py <target.sdf> 
#
#       * Uses default gazebo config : 'gazebo_config_template.json'
#       * Uses default feagi config : 'feagi_config_template.json'
#
# 2 - python config_parser.py <target.sdf> <gazebo_config.json> <feagi_config.json> 
#
#   * Both <gazebo_config.json> and <feagi_config.json> or the default files must be in the current directory to work properly *

# Description : used to parse the SDF to an XML structure which can be iterated through
# INPUT : file path (String)
# Output on success : XML tree
# Output on fail : None
def sdf_to_xml(fp):
    try:
        with open(fp, 'r') as f:
            sdf_content = f.read()

        if 'xmlns:gz' not in sdf_content:
            sdf_content = sdf_content.replace(
                '<sdf',
                '<sdf xmlns:gz="http://gazebosim.org/schema"',
                1
            )

        root = ET.fromstring(sdf_content)
        tree = ET.ElementTree(root)
        return tree

    except ET.XMLSyntaxError as e:
        print(f"Couldn't parse SDF file\n{e}")
        return None
    except FileNotFoundError:
        print(f"File couldn't be found: {fp}")
        return None

# Description : used to strip the XML tree of any unnecessary elements
# INPUT : tree element (expected to be the root)
# Output on success : XML tree
# Output on fail : None
def strip_tree (element, found_elements): 
    for child in element:
        #print(element.tag)
        if element.tag in g_config['allow_list'] and element not in found_elements:
            # if element.get('name') and element.get('type'):
            #     found_elements.append(element)
            if element.get('name'):
                found_elements.append(element)
        
        strip_tree(child, found_elements)        

# Description : used to recursively search the XML Tree structure for specefic elements by the element tag
# INPUT : the current element being searched for a match to the search tag
# Output on success : a refrence to the xml element with a tag matching 'search_tag'
# Output on fail : None
def find_element_by_tag(element, search_tag):
    # Check if current element matches
    if element.tag == search_tag:
        return element
    # Recursively check child elements
    for child in element:
        result = find_element_by_tag(child, search_tag)
        if result is not None:
            return result
    return None     

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

# Description : Find match for specific element in list of JSON elements
# INPUT : List of JSON elements, name of JSON element to find
# Output on success : JSON element
# Output on fail : None
def find_json_element(json_list, json_name):
    for json_elements in json_list:
        if json_elements['custom_name'] == json_name:
            return json_elements
        # Recursively check children
        result = find_json_element(json_elements['children'], json_name)
        if result is not None:
            return result
    return None

# Description : Changes existing JSON structure to account for parent child nesting
# INPUT : list of found elements, existing json list
# Output on success : Final nested JSON file
# Output on fail : None
def nest(found_elements, json_list):
    for xml_elements in found_elements:
        # Find tags for current element
        parent = find_element_by_tag(xml_elements, 'parent')
        child = find_element_by_tag(xml_elements, 'child')

        # Begin nesting 
        if child is not None:

            # Find child Json element
            json_child = find_json_element(json_list, child.text)
            
            if json_child:
                # Finds parent Json element
                json_parent = find_json_element(json_list, xml_elements.get('name'))

                if json_parent:
                    json_parent['children'].append(json_child)
                    json_list.remove(json_child)

        if parent is not None:
            json_child = find_json_element(json_list, xml_elements.get('name'))
            if json_child:
                json_parent = find_json_element(json_list, parent.text)
                if json_parent:
                    json_parent['children'].append(json_child)
                    json_list.remove(json_child)    

# Description : Locates any topic definitions in the sdf file
# INPUT : fp ~ file path to sdf file, topic_definitions ~ dictionary to contain mappings
# Output on success : updates "topic_definitions" to contain mappings from
#                             "joint_name" : "topic_name"
# Output on fail : "topic_definitions" is left empty
def find_topics(fp, topic_definitions):
    try:
        with open(fp, 'r') as f:
            sdf_content = f.read()

        # Ensure the namespace is defined
        if 'xmlns:gz' not in sdf_content:
            sdf_content = sdf_content.replace(
                '<sdf',
                '<sdf xmlns:gz="http://gazebosim.org/schema"',
                1
            )

        # Parse XML
        root = ET.fromstring(sdf_content)
        
        # Find all <plugin> elements
        for plugin in root.findall(".//plugin"):

            topic_element = plugin.find("topic")
            joint_element = plugin.find("joint_name")

            if topic_element is not None and topic_element.text:
                if joint_element is not None and joint_element.text:
                    topic_definitions[joint_element.text.strip()] = topic_element.text.strip()
                else:
                    topic_definitions[plugin.get('name')] = topic_element.text

    except Exception as e:
        print(f"Error: {e}")
        return []
    
# Description : Renames elements in the json list to the topic names
# INPUT : List of elements, current json list, list of topic names
# Output on success : Updates the custom name of the json list elements to be the topic name
# Output on fail : None
def rename_elements(found_elements, json_list, topic_definitions):
    for elements in found_elements:
        element_to_rename = find_json_element(json_list, elements.get('name'))

        if element_to_rename is not None:
            if element_to_rename['custom_name'] in topic_definitions:
                element_to_rename['custom_name'] = topic_definitions[elements.get('name')]
    return

# Description : Creates json items and adds to list without nesting
# INPUT : list of found elements, existing json list
# Output on success : Final nested JSON file
# Output on fail : None
def create_json(found_elements, json_list):
    index_number = 0
    # Loop through each found element from the SDF
    for elements in found_elements:

        # Check to see if element is plugin, and if plugin is in gazebo mapping list
        if elements.tag == 'plugin' and elements.get('name') not in g_config['plugin_output']:
            found_elements.remove
        else:
        # Create Vars for Sensor element
            if elements.get('type') in g_config['sensor']: # sensor
                # custom_name = elements.get('name')
                type = 'input'
                feagi_dev_type = g_config['sensor'][elements.get('type')]

            elif elements.get('type') in g_config['actuator']: # actuator
            # Create Vars for Actuator element 
                # custom_name = elements.get('name')
                type = 'output'
                feagi_dev_type = g_config['actuator'][elements.get('type')]

            elif elements.get('name') in g_config['plugin_output']:
                type = 'output'
                feagi_dev_type = g_config['plugin_output'][elements.get('name')]

            else: # link / body
            # Create Vars for links / bodys
                # custom_name = elements.get('name')
                type = 'body'
                feagi_dev_type = None

            # setting up general structure
            # Check to see if current element is plugin
            if elements.tag == 'plugin':
                parsed_name = elements.get('name').replace("gz::sim::systems::", "")
                topic_name = find_element_by_tag(elements, 'topic')
                if topic_name is not None:
                    toadd = {'custom_name': topic_name.text,
                            'type': type,
                            'description': "",
                            'children': []}
                else:
                    toadd = {'custom_name': parsed_name,
                            'type': type,
                            'description': "",
                            'children': []}
            else:
                toadd = {'custom_name': elements.get('name'),
                        'type': type,
                        'description': "",
                        'children': []}
            
            # handle device type and parameters/properties if sensor or actuator
            if feagi_dev_type is not None:
                # retrieve all properties necessary for sensor / actuator
                props = find_properties(feagi_dev_type, type)
                props["feagi_index"] = index_number
                # insert data into parameters/properties
                # TYPES ARE: gyro, servo, proximity, camera
                if feagi_dev_type == 'servo':
                    min = find_element_by_tag(elements, 'lower')
                    max = find_element_by_tag(elements, 'upper')
                    if min is not None:
                        props["min_value"] = float(min.text)
                    if max is not None:
                        props["max_value"] = float(max.text)
                    # calculate max power
                    range_value = abs(float(max.text) - float(min.text))
                    target_steps = 30  # Aim for about 30 steps
                    magnitude = math.log10(range_value)
                    increment = pow(10, magnitude) / 10
                    if range_value / increment > target_steps * 2:
                        increment *= 5
                    elif range_value / increment > target_steps:
                        increment *= 2
                    elif range_value / increment < target_steps / 2:
                        increment /= 2

                    if increment > 999999999:
                        increment = 999999999
                    props["max_power"] = increment
                    if abs(float(min.text)) > 200 or abs(float(max.text)) > 200:
                        feagi_dev_type = 'motor'

                elif feagi_dev_type == 'gyro':
                    pass
                elif feagi_dev_type == 'proximity':
                    min = find_element_by_tag(elements, 'min')
                    max = find_element_by_tag(elements, 'max')
                    if min is not None:
                        props["min_value"] = float(min.text)
                    if max is not None:
                        props["max_value"] = float(max.text)
                elif feagi_dev_type == 'camera':
                    camera_name = find_element_by_tag(elements, 'topic')
                    if camera_name is not None:
                        # toadd["custom_name"] = elements.get('name') + "_" + camera_name.text
                        toadd["custom_name"] = camera_name.text
                else:
                    pass
                
                # add in extra lines to dict
                temp = list(toadd.items())
                temp.insert(2, ('feagi device type', feagi_dev_type ))
                temp.insert(3, ('properties', props ))
                toadd = dict(temp)
                index_number += 1

            # add to json list that will be sent to file
            json_list.append(toadd)

    return

# Description : Strip data down to found paramaters from ignore list
# INPUT : Device type and xml element type
# Output on success : Dictionary
# Output on fail : None
def find_properties(devtype, ftype):
    # removes all properties on ignore_list
    properties_list = []
    start = f_config[ftype][devtype]["parameters"]
    for i in start:
        if i['label'] not in g_config['ignore_list']:

            if 'parameters' in i:
                littlelist = []
                for j in i['parameters']:
                    if j['label'] not in g_config['ignore_list']:
                        littlelist.append((j['label'], j['default']))
                properties_list.append((i['label'], dict(littlelist)))

            else:
                properties_list.append((i['label'], i['default']))

    toret = dict(properties_list)
    return toret

def main():
    # Will store all found elements
    found_elements = []

    # Stores mappings from joint names -> topics
    topic_definitions = {}

    num_args = len(sys.argv) - 1

    if num_args == 1:
        print('Parsing : ' + sys.argv[1])
        open_files('gazebo_config_template.json', 'feagi_config_template.json', sys.argv[1], found_elements)
    elif num_args == 3:
        print('Parsing : ' + sys.argv[1])
        open_files(sys.argv[2], sys.argv[3], sys.argv[1], found_elements)
    else :
        print("Incorrect command usage, please use either :\npython config_parser.py <target.sdf> <gazebo_config.json> <feagi_config.json>\npython config_parser.py <target.sdf>")
        return
    
    json_list = []

    file = open("model_config_tree.json", "w")

    # Finds all topic definitions, necessary for correct naming
    find_topics(sys.argv[1], topic_definitions)
    print("Definitions found : ", topic_definitions)


    # Creates un-nested json structure with all data from file
    create_json(found_elements, json_list)

    # Nests the children found in created Json structure
    nest(found_elements, json_list)

    rename_elements(found_elements, json_list, topic_definitions)

    json.dump(json_list, file, indent=4)
    file.close()
                 
    return

if __name__ =="__main__":
    main()

 

