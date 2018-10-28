import os
import expipe
import pathlib

try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml

settings = {}

def _is_in_project(path):
    local_root, local_config = _load_local_config(path)
    if local_root is None:
        return False
    return True

def _load_local_config(path):
    current_root = pathlib.Path(path)
    current_path = current_root / "expipe.yaml"
    if not current_path.exists():
        if current_root.match(current_path.root):
            return None, {}

        return load_local_config(current_root.parent)
    current_config = _load_config(current_path)
    return current_root, current_config

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
