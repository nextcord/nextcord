import re
from itertools import chain
from pathlib import Path

HEADLINE_RE = re.compile(r"\s*(?P<header>.+)\n\s*(?P<underline>-{2,}|={2,}|\+{2,}|~{2,})")
NEWLINE_RE = re.compile(r"\n")

path = Path(".")
globs = ("nextcord/**/*.py", "docs/**/*.rst")
files = chain(*(path.glob(glob) for glob in globs))


for file in files:
    with open(file, mode="r") as f:
        content = f.read()

        for match in HEADLINE_RE.finditer(content):
            if len(match.group("header")) != len(match.group("underline")):
                start_pos = match.start()
                line_no = len(NEWLINE_RE.findall(content, 0, start_pos)) + 3

                header = match.group("header")
                underline = match.group("underline")

                print(f"{file}#{line_no}:\n\t{header}\n\t{underline}\n")
