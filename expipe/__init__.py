from ._version import get_versions
from .config import configure, ensure_testing
from .io.core import get_project, require_project, delete_project
__version__ = get_versions()['version']
del get_versions
