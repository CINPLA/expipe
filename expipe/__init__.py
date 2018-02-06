from ._version import get_versions
from .config import configure, ensure_testing, settings
from .io.core import (get_project, require_project, delete_project,
                      get_template, require_template, delete_template)
# __version__ = get_versions()['version']
__version__ = "1.0"
del get_versions
