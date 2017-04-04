from xmljson import yahoo as yh
from xml.etree.ElementTree import fromstring
import json
import re
import expipe.io
import os
import sys

def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
odml_terminologies_path = sys.argv[1]

root_path = os.path.join(odml_terminologies_path, "v1.0")
print("This will upload and possibly overwrite all templates on the server. Are you sure? [y/N]:")
choice = input().lower()
if not choice in ["y", "yes", "ye"]:
    print("Aborting...")
    sys.exit(0)

for foldername in os.listdir(root_path):
    folder_path = os.path.join(root_path, foldername)
    if not os.path.isdir(folder_path):
        continue
    for filename in os.listdir(folder_path):
        print("FILENAME", filename)
        if not filename.endswith(".xml"):
            continue
        with open(os.path.join(folder_path, filename)) as f:
            xmldata = f.read()
            data = yh.data(fromstring(xmldata))
        
        if filename in ["blackrock.xml", "stimulusTypes.xml"]:
            continue
        
        name = foldername + "_" + filename.replace(".xml", "")

        data = data['odML']['section']
        result = {
            "definition": data["definition"],
            "name": data["name"]
        }
        try:
            properties = data["property"]
        except KeyError:
            print("ERROR on property")
            continue
            
        try:
            if not isinstance(properties, list):
                properties = [properties]
            for prop in properties:
                key = convert(prop["name"])
                value = prop["value"]
                result[key] = {
                    "definition": prop["definition"]
                }
                if isinstance(value, list):
                    alternatives = {}
                    for subval in value:
                        alternatives[subval["content"]] = True
                        subtype = subval["type"]  # TODO might change
                    result[key]["alternatives"] = alternatives
                    result[key]["type"] = subtype
                else:
                    result[key]["type"] = value["type"]
                result[key]["type"] = result[key]["type"].replace("text", "string")
                result[key]["value"] = ""

            template = {
                "identifier": name,
            }
            template_contents = result
            del(template_contents["name"])
            
            # upload to Firebase (WARNING: this overwrites any changes made on the server!)
            expipe.io.core.db.child("templates").child(name).set(template, expipe.io.core.user["idToken"])
            expipe.io.core.db.child("templates_contents").child(name).set(template_contents, expipe.io.core.user["idToken"])
        except Exception as e:
            print("ERROR on something")
            print(e)
