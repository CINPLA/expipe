import os
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .config import settings, configure, ensure_testing
