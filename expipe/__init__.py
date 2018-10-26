import warnings
import re
from ._version import get_versions
from .config import settings
from .core import require_project, create_project, get_project, delete_project
from . import backends
# __version__ = get_versions()['version']
__version__ = "1.0"
del get_versions

# DeprecationWarning should always be printed
warnings.filterwarnings(
    'always', category=DeprecationWarning,
    module=r'^{0}\.'.format(re.escape(__name__)))
