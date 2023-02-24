import contextlib

from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin


def get_version(version: str):
    # append version identifier based on commit count
    if all(v not in version for v in ("a", "b", "rc")):
        return
    with contextlib.suppress(Exception):
        import subprocess

        p = subprocess.Popen(
            ["git", "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, _ = p.communicate()
        if out:
            version += out.decode("utf-8").strip()
        p = subprocess.Popen(
            ["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, _ = p.communicate()
        if out:
            version += "+g" + out.decode("utf-8").strip()
    return version


class VersionerPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        io = application._io
        if not io or io.input.first_argument != "build":
            return
        if application.poetry.package.name != "nextcord":
            return
        if version := get_version(application.poetry.package.version.text):
            if application._io:
                application._io.write_line("Found nextcord, adjusting version")
            application.poetry.package._set_version(version)
