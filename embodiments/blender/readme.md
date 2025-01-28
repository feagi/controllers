# Blender
## Information
- Version: 4+
- Programming: Python using Blender API only
- Network: ZMQ, UDP, or WS

## Setup Instructions
1. Install Blender
   - Download the latest stable version from: https://www.blender.org/download/
   - Note: Blender supports all major platforms (Windows, macOS, and Linux)
   - The Python interpreter comes bundled with the Blender installation
2. Familiarize yourself with Blender Python (bpy)
   - Start with the quickstart guide: https://docs.blender.org/api/current/info_quickstart.html#before-starting
   - This guide will help you understand:
     - Python console usage in Blender
     - Basic script execution
     - Object manipulation
     - Animation control
3. Study the API Documentation
   - Reference: https://docs.blender.org/api/current/info_overview.html
   - Focus on these key areas:
     - Object creation and manipulation
     - Property access and modification
     - Animation system
     - Data blocks and scene management
     - Custom property handling
     - Event handling system
4. Implement FEAGI Controller
   - Access the controller documentation: https://github.com/feagi/controllers/blob/main/README.md
   - You will need to develop code that:
     - Interfaces with Blender's Python API
     - Processes FEAGI signals into Blender commands
     - Sends object/scene data back to FEAGI

## Controller
Boilerplates are provided. A controller requires capabilities, networking, requirements.txt, and version specifications.

## Libraries
Feagi-connector is the library that enables communication with the brain (FEAGI). We need to create a controller for Blender.

## Troubleshooting
- Join our [Discord community](https://chat.expo.dev) to chat with other users and ask questions
- If you encounter issues building the controller, please create an issue in the repository