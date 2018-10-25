import warnings
import re
from ._version import get_versions
from .config import settings
from .core import load_file_system, load_firebase, require_project
from . import backends
# __version__ = get_versions()['version']
__version__ = "1.0"
del get_versions

# DeprecationWarning should always be printed
warnings.filterwarnings(
    'always', category=DeprecationWarning,
    module=r'^{0}\.'.format(re.escape(__name__)))
