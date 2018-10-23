from ._version import get_versions
from .config import settings
from .core import load_file_system, load_firebase
from . import backends
# __version__ = get_versions()['version']
__version__ = "1.0"
del get_versions
