"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


from importlib import import_module
from pathlib import Path
from shutil import copyfile

with open(".aliasignorerc") as f:
    ignores = [line.strip() for line in f.readlines()]
with open("alias_license.py") as f:
    license_text = f.read()

print(f"Ignoring: {ignores}")

target_folder = Path("nextcord")
alias_folder = Path("discord")


def scan_dir(folder) -> None:
    for file in folder.glob("*"):
        unprefixed = str(file)[len("nextcord") + 1 :]
        should_ignore = False
        for ignore in ignores:
            if ignore.startswith("^"):
                if unprefixed.startswith(ignore[1:]):
                    should_ignore = True
                    break
            if ignore in unprefixed:
                should_ignore = True
                break
        if should_ignore:
            print(f"Ignoring {unprefixed}")
            continue
        if "__pycache__" in unprefixed:
            continue
        if file.is_file():
            file_extension = unprefixed.split(".")[-1]
            if file_extension == "py":
                # Should create an alias
                import_name = str(file)[:-3].replace("/", ".").replace("\\", ".")
                module = import_module(import_name)
                alias_file = ""

                # License text
                alias_file += license_text

                # Imports
                module_attrs = dir(module)
                attrs = []
                for attr in module_attrs:
                    if attr.startswith("__"):
                        continue
                    attrs.append(attr)
                if len(attrs) > 0:
                    alias_file += f"from {import_name} import {', '.join(attrs)}\n"

                # __all__
                module_all = getattr(module, "__all__", None)
                if module_all is not None:
                    module_all_quotes = ", ".join([f'"{item}"' for item in module_all])
                    module_all_out = f"__all__ = ({module_all_quotes})"

                    alias_file += module_all_out

                with (alias_folder / unprefixed).open("w+") as f:
                    f.write(alias_file)
            else:
                print(f"Copied {file}")
                copyfile(str(file), str(alias_folder / unprefixed))

        else:
            scan_dir(file)


scan_dir(target_folder)
