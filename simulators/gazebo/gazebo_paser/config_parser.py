import json
import sys
import os

def main():
    if len(sys.argv) != 3:
        print("Incorrect usage please use python config_parser.py <filename.sdf> <feagiTemplate.json>")
        return

    #begin opening files
    try:
        with open(sys.argv[2], 'r') as config:
            config_json = json.load(config)

    except FileNotFoundError:
        print("Couldn't open the feagi config template <" + sys.argv[2] + ">")
        quit()

    try:
        with open(sys.argv[1], 'r') as sdf:
            sdf_file = sdf.read()
            
    except FileNotFoundError:
        print("Couldn't open the target sdf file <" + sys.argv[1] + ">");
        quit()
    
    print(config_json)
    print(sdf_file)
    return

if __name__ =="__main__":
    main()



