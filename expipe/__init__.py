from ._version import get_versions
from .config import configure, ensure_testing, settings
from .core import (get_project, require_project, delete_project)
from . import backends
# __version__ = get_versions()['version']
__version__ = "1.0"
del get_versions
