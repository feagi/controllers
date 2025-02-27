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
        if element.tag in g_config['allow_list'] and element not in found_elements:
            # if element.get('name') and element.get('type'):
            #     found_elements.append(element)
            if element.get('name'):
                found_elements.append(element)
        
        strip_tree(child, found_elements)        
 
def find_element_by_tag(element, tag):
    # Check if current element matches
    if element.tag == tag:
        return element
    # Recursively check child elements
    for child in element:
        result = find_element_by_tag(child, tag)
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

def print_all(list):
    for element in list:
         print(element.tag)# + " name=" + element.get('name'))
         children = element.findall('*')
         print_all(children)

# Description : Take in list of elements found from SDF and convert into a json file
# INPUT : list of found elements, list of json object to be built
# Output on success : JSON Object
# Output on fail : None
def create_json(mylist, jlist):
    
    # Loop through each found element from the SDF
    for e in mylist:
        child_arr = []
        for child in e:
            if child in mylist:
                if child not in child_arr:
                    child_arr.append(child)
        #print(child_arr)

        if e not in child_arr:
            print(e.get('name'))
            for i in child_arr:
                print(child.get('name'))
            # Create Vars for Sensor element
            if e.get('type') in g_config['sensor']: # sensor
                custom_name = e.get('name')
                type = 'input'
                feagi_dev_type = g_config['sensor'][e.get('type')]
                #properties = {}
                description = ""
                children = []
                for i in child_arr:
                    children.append(create_child(i))

            elif e.get('type') in g_config['actuator']: # actuator
            # Create Vars for Actuator element 
                custom_name = e.get('name')
                type = 'output'
                feagi_dev_type = g_config['actuator'][e.get('type')]
                #properties = {}
                description = ""
                children = []
                for i in child_arr:
                    children.append(create_child(i))

            else: # link / body
            # Create Vars for links / bodys
                custom_name = e.get('name')
                type = e.tag
                feagi_dev_type = None
                #properties = {}
                description = ""
                children = []
                for i in child_arr:
                    children.append(create_child(i))

            # setting up general structure
            toadd = {'custom_name': custom_name,
                    'type': type,
                    'description': description,
                    'children': children}
            
            # handle device type and parameters/properties if sensor or actuator
            if feagi_dev_type is not None:
                # retrieve all properties necessary for sensor / actuator
                props = find_properties(feagi_dev_type, type)

                # insert data into parameters/properties
                # TYPES ARE: gyro, servo, proximity, camera
                if feagi_dev_type == 'servo':
                    min = find_element_by_tag(e, 'upper')
                    max = find_element_by_tag(e, 'lower')
                    if min is not None:
                        props["min_value"] = float(min.text)
                    if max is not None:
                        props["max_value"] = float(max.text)
                elif feagi_dev_type == 'gyro':
                    pass
                elif feagi_dev_type == 'proximity':
                    min = find_element_by_tag(e, 'min')
                    max = find_element_by_tag(e, 'max')
                    if min is not None:
                        props["min_value"] = float(min.text)
                    if max is not None:
                        props["max_value"] = float(max.text)
                elif feagi_dev_type == 'camera':
                    pass
                else:
                    pass

                # add in extra lines to dict
                temp = list(toadd.items())
                temp.insert(2, ('feagi device type', feagi_dev_type ))
                temp.insert(3, ('properties', props ))
                toadd = dict(temp)              

            # add to json list that will be sent to file
            jlist.append(toadd)

    return

def create_child(child):
        
    # Create Vars for Sensor element
        if child.get('type') in g_config['sensor']: # sensor
            custom_name = child.get('name')
            type = 'input'
            feagi_dev_type = g_config['sensor'][child.get('type')]
            #properties = {}
            description = ""
            children = []

        elif child.get('type') in g_config['actuator']: # actuator
        # Create Vars for Actuator element 
            custom_name = child.get('name')
            type = 'output'
            feagi_dev_type = g_config['actuator'][child.get('type')]
            #properties = {}
            description = ""
            children = []

        else: # link / body
        # Create Vars for links / bodys
            custom_name = child.get('name')
            type = child.tag
            feagi_dev_type = None
            #properties = {}
            description = ""
            children = []

        # setting up general structure
        child_data = {'custom_name': custom_name,
                'type': type,
                'description': description,
                'children': children}
        
        # handle device type and parameters/properties if sensor or actuator
        if feagi_dev_type is not None:
            # retrieve all properties necessary for sensor / actuator
            props = find_properties(feagi_dev_type, type)

            # insert data into parameters/properties
            # TYPES ARE: gyro, servo, proximity, camera
            if feagi_dev_type == 'servo':
                min = find_element_by_tag(child, 'upper')
                max = find_element_by_tag(child, 'lower')
                if min is not None:
                    props["min_value"] = float(min.text)
                if max is not None:
                    props["max_value"] = float(max.text)
            elif feagi_dev_type == 'gyro':
                pass
            elif feagi_dev_type == 'proximity':
                min = find_element_by_tag(child, 'min')
                max = find_element_by_tag(child, 'max')
                if min is not None:
                    props["min_value"] = float(min.text)
                if max is not None:
                    props["max_value"] = float(max.text)
            elif feagi_dev_type == 'camera':
                pass
            else:
                pass

            # add in extra lines to dict
            temp = list(child_data.items())
            temp.insert(2, ('feagi device type', feagi_dev_type ))
            temp.insert(3, ('properties', props ))
            child_data = dict(temp)              

        return child_data

# Description : Take in list of elements found from SDF and print into a json file
# INPUT : list of found elements
# Output on success : JSON file
# Output on fail : None
def print_json(mylist, jlist):
    
    file = open("model_config_tree.json", "w")
    create_json(mylist, jlist)
    json.dump(jlist, file, indent=4)
    file.close()
    
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
    
    file = open("model_config_tree_development.json", "w")

    for e in found_elements:
       if e.tag == 'joint':
           upper = find_element_by_tag(e, 'upper')
           lower = find_element_by_tag(e, 'lower')
            
           print("<" + e.tag + " name=" + e.get('name') + " type=" + e.get('type') + "> " )
           file.write("<" + e.tag + " name=" + e.get('name') + " type=" + e.get('type') + "> " + "\n")
           if upper != None and lower != None:
               print("Upper Limit : " + upper.text + "\nLower Limit : " + lower.text)
               file.write("Upper Limit : " + upper.text + "\nLower Limit : " + lower.text + "\n")
            
       elif e.tag == 'sensor':
           min = find_element_by_tag(e, 'min')
           max = find_element_by_tag(e, 'max')

           print("<" + e.tag + " name=" + e.get('name') + " type=" + e.get('type') + ">")
           file.write("<" + e.tag + " name=" + e.get('name') + " type=" + e.get('type') + ">" +"\n")
           if min != None and max != None:
               print("Min: " + min.text + "\nMax: " + max.text)
               file.write("Min: " + min.text + "\nMax: " + max.text +"\n")
       else:
           print("<" + e.tag + " name=" + e.get('name') + ">" )
           file.write("<" + e.tag + " name=" + e.get('name') + ">" +"\n")

    file.close()

    push_to_file = []

    print_json(found_elements, push_to_file)

    # for element in found_elements:
    #     print("<" + element.tag + " name=" + element.get('name') + ">")
    # print_all(found_elements)

             
    return

if __name__ =="__main__":
    main()



