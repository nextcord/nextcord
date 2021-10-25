import collections


_VersionInfo = collections.namedtuple("_VersionInfo", "year month day release serial")

version = "2021.4.13"
version_info = _VersionInfo(2021, 4, 13, "final", 0)
