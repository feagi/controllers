# Mujoco Parser
This README provides an overview of the **Mujoco Parser**, a tool designed to read any **XML (MuJoCo Model XML)** file and convert it into a structured configuration (`model_config_tree.json`). The parser facilitates the translation between **MuJoCo** and **FEAGI** capabilities while maintaining a ground truth for sensors and actuators. Additionally, it generates a necessary config without requiring extra manual work.

This document explains the parser's role, its relationship with other components (such as the **MuJoCo controller** and **FEAGI configurator**), and how it processes configuration templates. By following this guide, users will understand how the parser integrates with MuJoCo and FEAGI, ensuring flexibility and compatibility with various MuJoCo XML model files.

Here is the diagram:

![diagram.png](_static/diagram.png)


# How to Use Config Parser Library in demo.py
Replace `replace_file_name_here` with your filename to generate the config.