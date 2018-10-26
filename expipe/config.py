import os
import expipe
import pathlib

try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml

settings = {}

def _load_config(path):
    path = pathlib.Path(path)
    if not path.exists():
        return {}
    with path.open('r') as f:
        return yaml.safe_load(f)

def _load_config_by_name(config):
    config_path = pathlib.Path(config)

    if config_path.suffix == ".yaml" and config_path.exists():
        pass
    else:
        config_path = (pathlib.Path.home() / ".config" / "expipe" / config_path).with_suffix(".yaml")

    return _load_config(config_path)

def _extend_config(config):
    global settings
    result = settings.copy()
    result.update(config)
    return result


def reload_config():
    global settings
    config_path = pathlib.Path.home() / '.config' / 'expipe' / 'config.yaml'

    return _load_config(config_path)


reload_config()
