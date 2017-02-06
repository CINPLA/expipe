import yaml
import os
import sys

settings_file_path = os.path.join(os.path.expanduser('~'), '.config', 'expipe', 'config.yaml')
test_settings_file_path = os.path.join(os.path.expanduser('~'), '.config', 'expipe', 'test-config.yaml')

default_settings = {
    'data_path': os.path.join(os.path.join(os.path.expanduser('~'), 'expipe_data')),
    'firebase': {
        'email': '',
        'password': '',
        'config': {
            "apiKey": "",
            "authDomain": "",
            "databaseURL": "",
            "storageBucket": "",
        }
    }
}
    

def deep_verification(default, current, path=""):
    for key in default:
        next_path = key
        if path:
            next_path = path + "." + key
            
        if key not in current:
            print("WARNING: '{}' not found in settings.".format(next_path),
                  "Please rerun expipe.configure().")
        else:
            if isinstance(default[key], dict):
                if not isinstance(current[key], dict):
                    print("WARNING: Expected '{}' to be dict in settings.".format(next_path),
                          "Please rerun expipe.configure().")
                else:
                    deep_verification(default[key], current[key], path=next_path)


def configure(data_path, email, password, url_prefix, api_key):
    """
    The configure function creates a configuration file if it does not yet exist.
    Ask your expipe administrator about the correct values for the parameters.
    
    Parameters
    ----------
    data_path :
        path to where data files should be stored
    email :
        user email on Firebase server
    password :
        user password on Firebase server (WARNING: Will be stored in plain text!)
    url_prefix:
        prefix of Firebase server URL (https://<url_prefix>.firebaseio.com)
    api_key:
        Firebase API key
    """
    settings_directory = os.path.dirname(settings_file_path)
    
    if not os.path.exists(settings_directory):
        os.makedirs(settings_directory)
    current_settings = {}
    if os.path.exists(settings_file_path):
        with open(settings_file_path, "r") as settings_file:
            current_settings = yaml.load(settings_file)
    current_settings.update({
        "data_path": data_path,
        "firebase": {
            "email": email,
            "password": password,
            "config": {
                "apiKey": api_key,
                "authDomain": "{}.firebaseapp.com".format(url_prefix),
                "databaseURL": "https://{}.firebaseio.com".format(url_prefix),
                "storageBucket": "{}.appspot.com".format(url_prefix)
            }
        }
    })
    with open(settings_file_path, "w") as settings_file:
        yaml.dump(current_settings, settings_file, default_flow_style=False)


def ensure_testing():
    global settings
    with open(test_settings_file_path) as settings_file:
        settings = yaml.load(settings_file)
        deep_verification(default_settings, settings)
    assert("allow_tests" in settings and settings["allow_tests"])

try:
    with open(settings_file_path) as settings_file:
        settings = yaml.load(settings_file)
        deep_verification(default_settings, settings)
except FileNotFoundError:
    print("WARNING: No expipe configuration file found. Using default settings.",
          "Type the following for more information about creating a config file:\n\n",
          "\texpipe.configure?\n\n")
    settings = default_settings

if "unittest" in sys.modules.keys() or "_pytest" in sys.modules.keys() or "doctest" in sys.argv:
    ensure_testing()
