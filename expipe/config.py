import os

import yaml

import expipe

config_dir = os.path.join(os.path.expanduser('~'), '.config', 'expipe')
rc_file_path = os.path.join(config_dir, 'expiperc')


_default_rc = {
    'settings_file_path': os.path.join(config_dir, 'config.yaml'),
    'test_settings_file_path': os.path.join(config_dir, 'test-config.yaml')
}

if not os.path.exists(rc_file_path):
    with open(rc_file_path, "w") as f:
        yaml.dump(_default_rc, f, default_flow_style=False)
    rc_params = _default_rc
else:
    with open(rc_file_path, "r") as f:
        rc_params = yaml.load(f)


default_settings = {
    'data_path': os.path.join(os.path.join(os.path.expanduser('~'), 'expipe_data')),
    'database_version': 1,
    "username": "nobody",
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

debug_settings = {
    'allow_tests': 'true',
    'database_version': 1,
    'data_path': '/tmp/expipe_data',
    "username": "nobody",
    'firebase': {
        'email': 'debug-bot@cinpla.com',
        'password': 'noneed',
        'config': {
            'apiKey': 'AIzaSyBnbsraKxrO8zv1qVZeAvJR4fEWzExQhOM',
            'authDomain': 'expipe-debug.firebaseapp.com',
            'databaseURL': 'https://expipe-debug.firebaseio.com',
            'storageBucket': 'expipe-debug.appspot.com',
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
    settings_directory = os.path.dirname(rc_params['settings_file_path'])

    if not os.path.exists(settings_directory):
        os.makedirs(settings_directory)
    current_settings = {}
    if os.path.exists(rc_params['settings_file_path']):
        with open(rc_params['settings_file_path'], "r") as settings_file:
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
    with open(rc_params['settings_file_path'], "w") as settings_file:
        yaml.dump(current_settings, settings_file, default_flow_style=False)


def ensure_testing():
    if os.path.exists(rc_params['test_settings_file_path']):
        with open(rc_params['test_settings_file_path']) as settings_file:
            settings = yaml.load(settings_file)
            deep_verification(default_settings, settings)
    else:
        settings = debug_settings
    assert("allow_tests" in settings and settings["allow_tests"])
    expipe.settings = settings


class Settings:
    def __init__(self):
        self.settings = {}

    def ensure_init(self):
        try:
            with open(rc_params['settings_file_path']) as settings_file:
                settings = yaml.load(settings_file)
                deep_verification(default_settings, settings)
                self.settings = settings
                return True
        except FileNotFoundError:
            print("ERROR: No expipe configuration file found.",
                  "Type the following for more information about creating a config file:\n\n",
                  "\texpipe.configure?\n\n")
            return False

    def __getitem__(self, name):
        self.ensure_init()
        return self.settings[name]

    def __contains__(self, name):
        self.ensure_init()
        return name in self.settings

    def get(self, name):
        self.ensure_init()
        return self.settings.get(name)

settings = Settings()
