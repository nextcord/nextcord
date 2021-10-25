import sys


_ALL = {
    # This will be populated by loaded alternative converters at runtime
}


def py_allow(major: int, minor: int, micro: int) -> None:
    if sys.version_info < (major, minor, micro):
        raise RuntimeError(
            "This extension requires Python>={0}.{1}.{2}".format(major, minor, micro)
        )
