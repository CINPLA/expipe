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

        return _load_local_config(current_root.parent)
    current_config = _load_config(current_path)
    return current_root, current_config


def _load_config(path):
    path = pathlib.Path(path)
    if not path.exists():
        result = {}
    else:
        with path.open('r') as f:
            result = yaml.safe_load(f)
    return result


def _dump_config(path, contents):
    assert path.suffix == '.yaml'
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            contents, f,
            default_flow_style=False,
            allow_unicode=True,
            Dumper=yaml.RoundTripDumper)


def _load_config_by_name(config=None):
    config_home = pathlib.Path.home() / ".config" / "expipe"
    if config is None:
        config_path = (config_home / 'config').with_suffix('.yaml')
    else:
        config_path = pathlib.Path(config)

    if config_path.suffix == ".yaml" and config_path.exists():
        pass
    else:
        config_path = (config_home / config_path / config_path).with_suffix(".yaml")

    return _load_config(config_path)


def _dump_config_by_name(config=None, contents=None):
    assert contents is not None, '"contents" is required'
    config_home = pathlib.Path.home() / ".config" / "expipe"
    if config is None:
        config_path = (config_home / 'config').with_suffix('.yaml')
    else:
        config_path = pathlib.Path(config)

    if config_path.suffix == ".yaml" and config_path.exists():
        pass
    else:
        config_path = (config_home / config_path / config_path).with_suffix(".yaml")

    return _dump_config(config_path, contents)


def _merge_config(global_config, project_config, local_config):
  result = {**global_config, **project_config, **local_config}
  # special rule for plugins, and as we don't know a-priori that any of the
  # configs have plugins we have to check each of them
  if 'plugins' in result:
      plugins = [
          a for p in [global_config, project_config, local_config]
          for a in p.get('plugins') or []
      ]
      result.update({'plugins': plugins})

  return result


def reload_config():
    global settings
    settings = _load_config_by_name(None)


reload_config()
