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

def find_json_element_type(json_list, json_name, json_type):
    for json_elements in json_list:
        if json_elements['custom_name'] == json_name and json_elements['type'] == json_type:
            return json_elements
        # Recursively check children
        result = find_json_element_type(json_elements['children'], json_name, json_type)
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
            if json_child is not None:
                json_parent = find_json_element(json_list, parent.text)
                if json_parent is not None:
                    json_parent['children'].append(json_child)
                    if json_child in json_list:
                        json_list.remove(json_child)    

# Description : Locates any topic definitions in the sdf file
# INPUT : fp ~ file path to sdf file, topic_definitions ~ dictionary to contain mappings, 
# found_elements ~ list of found elements from gazebo config, sub_topic_definitions ~ dictionary to contain mappings
# Output on success : updates "topic_definitions" and "sub_topic_definitions" to contain mappings from
#                             "element" : "topic_name"
# Output on fail : "topic_definitions" is left empty
def find_topics(fp, topic_definitions, found_elements, sub_topic_definitions):
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

            sub_topic_element = plugin.find("sub_topic")
            
            if sub_topic_element is not None and sub_topic_element.text:
                sub_topic_definitions[sub_topic_element.text] = plugin.get('name')

        # Search elements for topics
        for element in found_elements:

            topic_element = element.find("topic")

            if topic_element is not None and topic_element.text:
                if element is not None and element.get('name'):
                    topic_definitions[element.get('name')] = topic_element.text.strip()

    except Exception as e:
        print(f"Error: {e}")
        return []
    
# Description : Renames elements in the json list to the topic names
# INPUT : List of elements, current json list, list of topic names
# Output on success : Updates the custom name of the json list elements to be the topic name
# Output on fail : None
def rename_elements(found_elements, json_list, topic_definitions, sub_topic_definitions):
    for elements in found_elements:
        element_to_rename = find_json_element(json_list, elements.get('name'))

        if element_to_rename is not None:
            if element_to_rename['type'] == 'body':
                output_element_to_rename = find_json_element_type(json_list, elements.get('name'), 'output')
                input_element_to_rename = find_json_element_type(json_list, elements.get('name'), 'input')
                if output_element_to_rename is None and input_element_to_rename is not None:
                    element_to_rename = input_element_to_rename
                elif output_element_to_rename is not None and input_element_to_rename is None:
                    element_to_rename = output_element_to_rename
        
        if element_to_rename is not None:
            if element_to_rename['custom_name'] in topic_definitions:
                existing_element = find_json_element(json_list, topic_definitions[elements.get('name')])
                if existing_element is None:
                    element_to_rename['custom_name'] = topic_definitions[elements.get('name')]
                else:
                    if element_to_rename['custom_name'] != topic_definitions[elements.get('name')]:
                        if element_to_rename['type'] != "body":
                            element_to_rename['type'] = "body"
                            del element_to_rename['properties']
                            del element_to_rename['feagi device type']
            
            # Any sensor/actuator not included in topics is converted to 'body'

            elif element_to_rename['custom_name'] not in topic_definitions and element_to_rename['custom_name'] not in sub_topic_definitions:
                if element_to_rename['type'] != "body":
                    element_to_rename['type'] = "body"
                    del element_to_rename['properties']
                    del element_to_rename['feagi device type']
    return

# Description : Removes elements that contain a sub_topic to another element from the json list
# INPUT : List of elements, current json list, sub topic mappings
# Output on success : Updates the json list to no longer contain the removed element
# Output on fail : None
def remove_element(sub_topic_definitions, found_elements, json_list):
     for element in found_elements:
        element_index = 0
        if element.get('name') in sub_topic_definitions:
            element_to_remove = find_json_element(json_list, sub_topic_definitions[element.get('name')])

            if element_to_remove is not None:
                while json_list[element_index]['custom_name'] is not element_to_remove['custom_name']:
                    element_index += 1
                del json_list[element_index]

# Description : Updates the feagi index values based on the newly changed json elements
# INPUT : list of found elements, existing json list
# Output on success : Updated feagi index values
# Output on fail : None
def index_elements(found_elements, json_list, topic_definitions):
    index_mapping = {}
    for element in found_elements:
        if element.tag != 'model':
            element_to_index = find_json_element(json_list, element.get('name'))
            if element_to_index is not None:
                if element_to_index['custom_name'] in topic_definitions:
                    renamed_element = find_json_element(json_list, topic_definitions[element.get('name')])
                    element_to_index = renamed_element

            if element_to_index is not None:
                if element_to_index['type'] != 'body':
                    if element_to_index['feagi device type'] in index_mapping:
                        index_mapping[element_to_index['feagi device type']] = int(index_mapping[element_to_index['feagi device type']]) + 1
                        element_to_index['properties']["feagi_index"] = int(index_mapping[element_to_index['feagi device type']])
                    else:
                        index_mapping[element_to_index['feagi device type']] = 0
                        element_to_index['properties']["feagi_index"] = 0  
    
    

# Description : Creates json items and adds to list without nesting
# INPUT : list of found elements, existing json list
# Output on success : Final nested JSON file
# Output on fail : None
def create_json(found_elements, json_list, topic_definitions):
    index_mapping = {}

    # Loop through each found element from the SDF
    for elements in found_elements:
        # Check to see if element is plugin, and if plugin is in gazebo mapping list
        if elements.tag == 'plugin' and elements.get('name') not in g_config['plugin_output']:
            if elements.get('name') in topic_definitions:
                del topic_definitions[elements.get('name')]
            found_elements.remove
        elif elements.tag == 'model':
                model_name = elements.get('name')
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

            elif elements.get('name') in g_config['plugin_input']:
                type = 'input'
                feagi_dev_type = g_config['plugin_input'][elements.get('name')]

            else: # link / body
            # Create Vars for links / bodys
                # custom_name = elements.get('name')
                type = 'body'
                feagi_dev_type = None

            # setting up general structure
            # Check to see if current element is plugin
            if elements.tag == 'plugin':
                parsed_name = elements.get('name')
                topic_name = find_element_by_tag(elements, 'topic')

                if parsed_name in g_config['topic_rename']:
                    rename = 'model/' + model_name + '/' + g_config['topic_rename'][elements.get('name')]
                    parsed_name = rename
                    print("Conflicting names defaulting to : ", rename)
                
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

                # insert data into parameters/properties
                # TYPES ARE: gyro, servo, proximity, camera
                if feagi_dev_type == 'servo':
                    min = find_element_by_tag(elements, 'lower')
                    i_min = find_element_by_tag(elements, 'i_min')
                    max = find_element_by_tag(elements, 'upper')
                    i_max = find_element_by_tag(elements, 'i_max')
                    if min is not None:
                        props["min_value"] = float(min.text)
                    elif i_min is not None:
                        min = i_min
                        props["min_value"] = float(min.text)

                    if max is not None:
                        props["max_value"] = float(max.text)
                    elif i_max is not None:
                        max = i_max
                        props["max_value"] = float(max.text)

                    # calculate max power
                    if min is not None and max is not None:
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
                            props["rolling_window_len"] = 2

                elif feagi_dev_type == 'gyro':
                    pass
                elif feagi_dev_type == 'lidar':
                    min = find_element_by_tag(elements, 'min')
                    max = find_element_by_tag(elements, 'max')
                    width = find_element_by_tag(elements, 'horizontal')
                    height = find_element_by_tag(elements, 'vertical')
                    if width is not None:
                        width_value = find_element_by_tag(width, 'samples')
                        if width_value is not None:
                            props["width"] = float(width_value.text)
                    if height is not None:
                        height_value = find_element_by_tag(height, 'samples')
                        if height_value is not None:
                            props["height"] = float(height_value.text)
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

                if feagi_dev_type in index_mapping:
                    index_mapping[feagi_dev_type] = int(index_mapping[feagi_dev_type]) + 1
                    props["feagi_index"] = int(index_mapping[feagi_dev_type])
                else:
                    index_mapping[feagi_dev_type] = 0
                    props["feagi_index"] = 0

                # add in extra lines to dict
                temp = list(toadd.items())
                temp.insert(2, ('feagi device type', feagi_dev_type ))
                temp.insert(3, ('properties', props ))
                toadd = dict(temp)

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
    sub_topic_definitions = {}

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
    find_topics(sys.argv[1], topic_definitions, found_elements, sub_topic_definitions)

    # Creates un-nested json structure with all data from file
    create_json(found_elements, json_list, topic_definitions)

    # Nests the children found in created Json structure
    nest(found_elements, json_list)

    rename_elements(found_elements, json_list, topic_definitions, sub_topic_definitions)

    remove_element(sub_topic_definitions, found_elements, json_list)

    index_elements(found_elements, json_list, topic_definitions)

    json.dump(json_list, file, indent=4)
    file.close()
                 
    return

if __name__ =="__main__":
    main()

 

