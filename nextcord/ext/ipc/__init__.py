import collections

from .client import Client
from .server import Server
from .errors import *


_VersionInfo = collections.namedtuple("_VersionInfo", "major minor micro release serial")

version = "1.0.0"
version_info = _VersionInfo(1, 0, 0, "final", 0)
