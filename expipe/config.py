import os
import expipe
import pathlib

try:
    import ruamel.yaml as yaml
except ImportError:
    import ruamel_yaml as yaml


def _load_config_by_name(folder, config):
    config_path = pathlib.Path(config)

    if config_path.suffix == ".yaml" and config_path.exists():
        pass
    else:
        config_path = (pathlib.Path.home() / ".config" / "expipe" / folder / config_path).with_suffix(".yaml")

    if not config_path.exists():
        raise FileNotFoundError("Could not load config '{}'. Please make sure the following config file exists:\n{}".format(config, config_path))

    with open(config_path) as f:
        return yaml.safe_load(f)


def _extend_config(config):
    global settings
    result = settings.copy()
    result.update(config)
    return result


def reload_config():
    global settings
    config_dir = pathlib.Path.home() / '.config' / 'expipe'
    config_file = config_dir / 'config.yaml'

    settings = {}

    if config_file.exists():
        with open(config_file) as f:
            settings = yaml.safe_load(f)


reload_config()
