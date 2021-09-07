from pathlib import Path
from importlib import import_module
from time import sleep

with open(".aliasignorerc") as f:
    ignores = [line.strip() for line in f.readlines()]
with open("alias_license.py") as f:
    license_text = f.read()

print(f"Ignoring: {ignores}")

target_folder = Path("nextcord")
alias_folder = Path("discord")


def scan_dir(folder):
    for file in folder.glob("*"):
        unprefixed = str(file)[len("nextcord") + 1:]
        if unprefixed in ignores:
            continue
        if file.is_file():
            if not unprefixed.endswith(".py"):
                continue
            # Should create a alias
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
                module_all_quotes = ", ".join([f"\"{item}\"" for item in module_all])
                module_all_out = f"__all__ = ({module_all_quotes})"

                alias_file += module_all_out

            with (alias_folder / unprefixed).open("w+") as f:
                f.write(alias_file)
        else:
            scan_dir(folder / unprefixed)


scan_dir(target_folder)
