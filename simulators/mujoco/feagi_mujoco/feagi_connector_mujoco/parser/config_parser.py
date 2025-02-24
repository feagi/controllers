import json
import math
import copy
import mujoco.viewer
import feagi_connector_mujoco
import xml.etree.ElementTree as ET

xml_actuators_type = dict()

current_path = feagi_connector_mujoco.parser.__path__
with open(str(current_path[0]) + '/mujoco_config_template.json', 'r') as f:
    config = json.load(f)
TRANSMISSION_TYPES = config['actuator']
SENSING_TYPES = config['sensor']
sensor_tag_to_name = config['sensor_tag_to_name']


def validate_name(name):
    symbols = ['/', '\\']
    for i in symbols:
        if i in name:
            name = name.replace(i, '_')
    return name


def generate_actuator_list(model, xml_actuators_type):
    actuator_information = {}
    counter = 0
    for i in range(model.nu):
        actuator_name = model.actuator(i).name
        if actuator_name == '':
            actuator_name = "actuator_" + str(counter)
            counter += 1
        actuator_name = validate_name(actuator_name)
        actuator_type = xml_actuators_type['output'][actuator_name]['type']
        actuator_information[actuator_name] = {"type": actuator_type, "range": model.actuator_ctrlrange[i]}
    return actuator_information


def generate_sensor_list(model, xml_actuators_type):
    return xml_actuators_type['input']


def check_nest_file_from_xml(xml_path):
    root, tree=xml_type_check(xml_path)

    # Store file paths
    files = [xml_path]

    # Find all include elements directly
    include_elements = root.findall('.//include')

    if include_elements:
        for include in include_elements:
            file_path = include.get('file')
            if file_path:
                print("Found included file:", file_path)
                files.append(file_path)
    return files


def check_nest_file_from_xml_string(xml_string):
    root, tree = xml_type_check(xml_string)

    # Store file paths
    files = [root]

    # Find all include elements directly
    include_elements = root.findall('.//include')

    if include_elements:
        for include in include_elements:
            file_path = include.get('file')
            if file_path:
                print("Found included file:", file_path)
                files.append(file_path)
    return files

def get_actuators(files):
    # Store actuator information in a dictionary
    actuators = {'output': {}}
    counter = 0
    for xml_path in files:
        # Parse the XML file
        root, tree = xml_type_check(xml_path)

        # Find the actuator section
        actuator_section = root.find('actuator')

        if actuator_section is not None:
            # Get all children of actuator section (all types of actuators)
            for actuator in actuator_section:
                name = actuator.get('name')
                if name is None:
                    name = "actuator_" + str(counter)
                    counter += 1
                name = validate_name(name)
                actuators['output'][name] = {'type': actuator.tag}
    return actuators


def get_sensors(files, sensors):
    sensors['input'] = {}
    for xml_path in files:
        # Parse the XML file
        root, tree = xml_type_check(xml_path)

        # Find the sensor section
        sensor_section = root.find('sensor')

        if sensor_section is not None:
            # Get all children of sensor section (all types of sensors)
            for sensor in sensor_section:
                if sensor.tag in sensor_tag_to_name:
                    name = sensor_tag_to_name[sensor.tag]
                    sensors['input'][name] = {'type': sensor.tag}

                    # Get all attributes of the sensor
                    for attr_name, attr_value in sensor.attrib.items():
                        if attr_name != 'name':  # Skip name as we already stored it
                            sensors['input'][name][attr_name] = attr_value

                    # Get text content if it exists
                    if sensor.text and sensor.text.strip():
                        sensors['input'][name]['value'] = sensor.text.strip()
                else:
                    print(sensor.tag, " is not supported yet.")
    return sensors

def calculate_increment(min_value, max_value):
    range_value = abs(max_value - min_value)
    target_steps = 30  # Aim for about 30 steps
    magnitude = int(math.log10(range_value))
    increment = pow(10, magnitude) / 10
    if range_value / increment > target_steps * 2:
        increment *= 5
    elif range_value / increment > target_steps:
        increment *= 2
    elif range_value / increment < target_steps / 2:
        increment /= 2
    return increment


def xml_type_check(xml_data):
    if isinstance(xml_data, str):
        tree = ET.parse(xml_data)
        root = tree.getroot()
    elif isinstance(xml_data, ET.Element):
        tree = ET.tostring(xml_data, encoding='utf8')
        root = ET.fromstring(tree)
    return root, tree


def generate_config(element, actuator_list, sensor_list, dict_increment):
    ignore_list = config['ignore_list']
    part_config = {'custom_name': element.attrib.get('name'), 'type': element.tag, 'feagi device type': None,
                   'properties': {},
                   'description': '', 'children': []}
    with open(str(current_path[0]) + "/feagi_config_template.json", "r") as f:
        template = json.load(f)

    if part_config['custom_name'] in actuator_list:
        part_config['feagi device type'] = TRANSMISSION_TYPES[actuator_list[part_config['custom_name']]['type']]
        part_config['type'] = 'output'
        part_config['properties'] = {}
        if part_config['feagi device type'] not in dict_increment:
            dict_increment[part_config['feagi device type']] = 0
        else:
            dict_increment[part_config['feagi device type']] += 1
        for parameter_list in template['output'][part_config['feagi device type']]['parameters']:
            if parameter_list['label'] not in ignore_list:
                part_config['properties'][parameter_list['label']] = parameter_list['default']
                if parameter_list['label'] == 'max_value' and part_config['feagi device type'] == 'servo':
                    part_config['properties'][parameter_list['label']] = \
                        actuator_list[part_config['custom_name']]['range'][1]
                elif parameter_list['label'] == 'min_value' and part_config['feagi device type'] == 'servo':
                    part_config['properties'][parameter_list['label']] = \
                        actuator_list[part_config['custom_name']]['range'][0]
                elif parameter_list['label'] == 'max_power' and part_config['feagi device type'] == 'servo':
                    part_config['properties'][parameter_list['label']] = calculate_increment(
                        actuator_list[part_config['custom_name']]['range'][0],
                        actuator_list[part_config['custom_name']]['range'][1])
                if parameter_list['label'] == 'max_power' and part_config['feagi device type'] == 'motor':
                    part_config['properties'][parameter_list['label']] = \
                        actuator_list[part_config['custom_name']]['range'][1]
                if parameter_list['label'] == 'feagi_index':
                    part_config['properties'][parameter_list['label']] = dict_increment[
                        part_config['feagi device type']]
    elif part_config['custom_name'] in sensor_list or part_config['type'] in sensor_list:
        get_type = ""
        for x in sensor_list:
            for key in sensor_list[x]:
                if part_config['custom_name'] in sensor_list[x][key]:
                    get_type = sensor_list[x]['type']
                    break
        part_config['feagi device type'] = SENSING_TYPES[get_type]
        if part_config['feagi device type'] not in dict_increment:
            dict_increment[part_config['feagi device type']] = 0
        else:
            dict_increment[part_config['feagi device type']] += 1

        part_config['type'] = 'input'
        part_config['properties'] = {}
        for parameter_list in template['input'][part_config['feagi device type']]['parameters']:
            if parameter_list['label'] not in ignore_list:
                if 'default' in parameter_list:
                    part_config['properties'][parameter_list['label']] = parameter_list['default']
    else:
        del part_config['feagi device type']
        del part_config['properties']
        part_config['type'] = 'body'

    # Recursively process children
    for child in list(element):
        child_config = generate_config(child, actuator_list, sensor_list, dict_increment)  # inception movie
        if child.tag in config['allow_list']:  # whatever gets the ball rolling
            part_config['children'].append(child_config)

    return part_config  # Important to return the config!


def mujoco_tree_config(xml_file, actuator_list, sensor_list):
    configs = []  # List to store configurations for each file
    feagi_index_increment = {}

    for xml_path in xml_file:
        root, tree = xml_type_check(xml_path)
        worldbody = root.findall('.//worldbody')
        if isinstance(tree, bytes):
            tree = ET.fromstring(tree)
            include_elements = tree
        else:
            include_elements = tree.getroot()
        if include_elements.tag == 'mujocoinclude':
            body_elements = include_elements
        else:
            body_elements = worldbody

        for body in body_elements:
            for element in list(body):
                body_config = generate_config(element, actuator_list, sensor_list, feagi_index_increment)
                configs.append(body_config)

    return configs


def convert_dict_to_json(configs):
    return json.dumps(configs)


def obtain_xml(xml):
    return xml


def update_actuator_and_sensor(xml_file):
    model = mujoco.MjModel.from_xml_path(xml_file)
    files = check_nest_file_from_xml(xml_file)
    xml_info = get_actuators(files)
    xml_info = get_sensors(files, xml_info)
    return model, xml_info, files


def update_actuator_and_sensor_with_string_input(xml_file_string):
    model = mujoco.MjModel.from_xml_string(xml_file_string)
    xml_data = ET.fromstring(xml_file_string)
    files = check_nest_file_from_xml_string(xml_data)
    xml_info = get_actuators(files)
    xml_info = get_sensors(files, xml_info)
    return model, xml_info, files


def save_file_as_json(data, file="model_config_tree.json"):
    print("saved to ", file)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def xml_file_to_config(xml_file):
    model, xml_actuators_type, files = update_actuator_and_sensor(xml_file)

    # Just obtain the actuator list that mujoco_tree_config needs
    actuator_information = generate_actuator_list(model, xml_actuators_type)

    # Just obtain the sensor list that mujoco_tree_config needs
    sensor_information = generate_sensor_list(model, xml_actuators_type)

    config_dict = mujoco_tree_config(files, actuator_information, sensor_information)  # get dict of config

    save_file_as_json(config_dict)

    # This is where you just send json to anywhere.
    return convert_dict_to_json(config_dict)


def raw_xml_string_to_config(string_xml_file):
    model, xml_actuators_type, files = update_actuator_and_sensor_with_string_input(string_xml_file)

    # Just obtain the actuator list that mujoco_tree_config needs
    actuator_information = generate_actuator_list(model, xml_actuators_type)

    # Just obtain the sensor list that mujoco_tree_config needs
    sensor_information = generate_sensor_list(model, xml_actuators_type)

    config_dict = mujoco_tree_config(files, actuator_information, sensor_information)  # get dict of config

    save_file_as_json(config_dict)

    # This is where you just send json to anywhere.
    return convert_dict_to_json(config_dict)
