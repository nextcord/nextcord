from abc import ABC, abstractmethod
from typing import Optional, Callable
from re import compile as compile_regex

slash_command_name_regex = compile_regex(r"^[\w-]{1,32}$")


class InteractionCommand(ABC):
    def __init__(self, callback, id: int, name: str, guild_id: Optional[int] = None, default_permission: bool = True) -> None:
        self.callback = callback
        self.id = id
        self.__name = name
        self.guild_id = guild_id
        self.default_permission = default_permission

    @abstractmethod
    def _validate_name(self, name: str) -> str:
        """Check that the given name is a valid name for this type of interaction, and possibly change the name to make it comply with the restrictions.

        Args:
            name (str): The name to check.

        Raises:
            TypeError: If the given name is invalid for this type of interaction.

        Returns:
            str: The same name if the name was valid, or a modified name if it was able to change it to comply with the restrictions.
        """
        pass

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def set_name(self, name: str):
        self.__name = self._validate_name(name)


class SlashCommand(InteractionCommand):
    def __init__(self, command: Callable, command_name: Optional[str] = None, description: Optional[str] = None):
        super().__init__(command, )
        self.callback = command
        if command_name is None:
            command_name = self.callback.__name__
        if description is None:
            self.description = self.callback.__doc__.replace(
                "  ", "").replace("     ", "").strip()

    def _extract_props(self):
        props = getattr(self.callback, "_command_props", None)
        if props is None:
            return
        if not isinstance(props, dict):
            raise TypeError(
                "Slash command properties have been incorrectly set!")

    def _validate_name(self, name: str):
        name = name.lower()
        if slash_command_name_regex.match(name.lower()) is None:
            raise TypeError(
                r"Slash command names have to match the regex `^[\w-]{1,32}$`")
        return name
