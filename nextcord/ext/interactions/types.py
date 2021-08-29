from typing import Optional, Callable
from re import compile as compile_regex

slash_command_name_regex = compile_regex(r"^[\w-]{1,32}$")

class InteractionCommand():
    id: Optional[int] = None
    guild_id: Optional[int] = None
    _name: str
    default_permission: bool = True
    callback: Callable

class SlashCommand(InteractionCommand):
    def __init__(self, command: Callable, command_name: Optional[str] = None, description: Optional[str] = None):
        self.callback = command
        if command_name is None:
            command_name = self.callback.__name__
        if description is None:
            self.description = self.callback.__doc__.replace("  ", "").replace("     ", "").strip()
    def _extract_props(self):
        props = getattr(self.callback, "_command_props", None)
        if props is None:
            return
        if not isinstance(props, dict):
            raise TypeError("Slash command properties have been incorrectly set!")




    @property
    def name(self):
        return self._name

    @name.setter
    def set_name(self, name: str):
        name = name.lower()
        if slash_command_name_regex.match(name) is None:
            raise TypeError(r"Slash command names have to match the regex `^[\w-]{1,32}$`")
        self._name = name

        

