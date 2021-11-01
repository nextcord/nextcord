from __future__ import annotations
from typing import TYPE_CHECKING, Union, Optional, List, Tuple
from . import utils
from .enums import ApplicationCommandType, ApplicationCommandOptionType
from .mixins import Hashable

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState


__all__ = (
    'ApplicationCommandResponseOptionChoice',
    'ApplicationCommandResponseOption',
    'ApplicationCommandResponse'
)


class ApplicationCommandResponse(Hashable):
    """Represents the response that Discord sends back when asked about Application Commands.

    Attributes
    ----------
    id: :class:`int`
        Discord ID of the Application Command.
    type: :class:`nextcord.ApplicationCommandType`
        Enum corresponding to the Application Command type. (slash, message, user)
    guild_id: Optional[:class:`int`]
        The Guild ID associated with the Application Command. If None, it's a global command.
    name: :class:`str`
        Name of the Application Command.
    description: :class:`str`
        Description of the Application Command.
    options: List[:class:`nextcord.ApplicationCommandResponseOption`]
        A list of options or subcommands that the Application Command has.
    default_permission: :class:`bool`
        If the command is enabled for users by default.
    """

    def __init__(self, state: ConnectionState, payload: dict):
        self._state: ConnectionState = state
        self.id: int = int(payload["id"])
        self.type: ApplicationCommandType = ApplicationCommandType(payload["type"])
        self.guild_id: Optional[int] = utils._get_as_snowflake(payload, "guild_id")
        self.name: str = payload["name"]
        self.description: str = payload["description"]
        self.options: List[
            ApplicationCommandResponseOption
        ] = ApplicationCommandResponseOption._create_options(payload.get("options", []))
        self.default_permission: Optional[bool] = payload.get(
            "default_permission", True
        )

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: Returns the :class:`Guild` associated with this Response, if any."""
        return self._state._get_guild(self.guild_id)

    @property
    def signature(self) -> Tuple[str, int, Optional[int]]:
        """Returns a simple high level signature of the command.

        Returns
        -------
        name: :class:`str`
            Name of the Application Command.
        type: :class:`int`
            Discord's integer value of the Application Command type
        guild_id: Optional[:class:`int`]
            The Guild ID associated with the Application Command. If None, it's a global command.
        """
        return self.name, self.type.value, self.guild_id


class ApplicationCommandResponseOptionChoice:
    """Represents a single choice in a list of options.

    Attributes
    ----------
    name: :class:`str`
        Name of the choice, this is what users see in Discord.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        Value of the choice, this is what Discord sends back to us.
    """

    def __init__(self, payload: Optional[dict] = None):
        if not payload:
            payload = {}
        self.name: str = payload.get('name')
        self.value: Union[str, int, float] = payload.get('value')


class ApplicationCommandResponseOption:
    """Represents an argument/parameter/option or subcommand of an Application Command.

    Attributes
    ----------
    type: :class:`ApplicationCommandOptionType`
        Enum corresponding to the Application Command Option type. (subcommand, string, integer, etc.)
    name: :class:`str`
        Name of the option or subcommand.
    description: :class:`str`
        Description of the option or subcommand.
    required: :class:`bool`
        If this option is required for users or not.
    """

    def __init__(self, payload: dict):
        self.type = ApplicationCommandOptionType(int(payload["type"]))
        self.name: str = payload['name']
        self.description: str = payload['description']
        self.required: Optional[bool] = payload.get('required')
        self.choices: List[ApplicationCommandResponseOptionChoice] = self._create_choices(payload.get('choices', []))
        self.options: List[ApplicationCommandResponseOption] = self._create_options(payload.get('options', []))

    @staticmethod
    def _create_choices(data: List[dict]) -> List[ApplicationCommandResponseOptionChoice]:
        return [ApplicationCommandResponseOptionChoice(raw_choice) for raw_choice in data]

    @staticmethod
    def _create_options(data: List[dict]) -> List[ApplicationCommandResponseOption]:
        return [ApplicationCommandResponseOption(raw_option) for raw_option in data]
