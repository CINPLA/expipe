import yaml
import os

settings_file_path = os.path.join(os.path.expanduser('~'), '.config', 'expipe', 'config.yaml')


def configure(data_path, email, password, overwrite=False):
    """
    The configure function creates a configuration file if it does not yet exist.
    
    It can be run similarly to this:
    
        expipe.configure(data_path="/media/norstore/server")
        
    Please see the above signature for the available options.
    """    
    settings_directory = os.path.dirname(settings_file_path)
    if os.path.exists(settings_file_path) and not overwrite:
        raise IOError("Configuration file already exists. "
                      "Use overwrite=True to allow it to be overwritten.")
    
    if not os.path.exists(settings_directory):
        os.makedirs(settings_directory)
    with open(settings_file_path, "w") as settings_file:
        yaml.dump({
            "data_path": data_path,
            "firebase": {
                "email": email,
                "password": password
            }
        }, settings_file)


default_settings = {
    'data_path': os.path.join(os.path.join(os.path.expanduser('~'), 'expipe_data'))
}

try:
    with open(settings_file_path) as settings_file:
        settings = yaml.load(settings_file)
except FileNotFoundError:
    print("INFO: No expipe configuration file found. Using default settings. "
          "Type the following for more information about creating a config file:\n\n"
          "\texpipe.configure?\n\n")
    settings = default_settings
