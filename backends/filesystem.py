from ..backend import *

class FileSystemBackend(AbstractBackend):
    def __init__(self, path):
        super(FileSystemBackend, self).__init__(
            path=path
        )

        self.path = pathlib.Path(path)
        self.root, self.config = self.discover_config(path)

    def discover_config(self, path):
        current_path = pathlib.Path(path)
        config_filename = current_path / "expipe.yaml"

        if not os.path.exists(config_filename):
            if current_path == pathlib.root:
                raise Exception("ERROR: No expipe.yaml found in current folder or parents.")

            return discover_config(current_path.parent())

        with open(config_filename) as f:
            return current_path, yaml.load(f)


