from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from .base import Interaction

__all__ = ("ApplicationCommandInteraction", "ApplicationAutocompleteInteraction", "SlashOptionData")

if TYPE_CHECKING:
    from ..application_command import (
        BaseApplicationCommand,
        SlashApplicationSubcommand,
    )
    from ..state import ConnectionState
    from ..types.interactions import Interaction as InteractionPayload


# class is here due to circular import issues
class SlashOptionData:
    """A class that contains data for an application command option.

    These classes are only created for options that a user defined.
    Thus, application command options that are not required, and weren't
    given a value by a user will not have a dedicated instance of this class.

    This class is for data recieving only! To create slash options, use :class:`SlashOption`.

    Parameters
    ----------
    data: :class: Dict[Union[`str`, `int`, `bool`]]
        The raw data for an option.
    value: Union[`str`, `int`, `float`, `bool`]
        Returns the user input value.
    type: :class:`int`
        The type of the application command option. This indicates what value the option accepts as an input
    name: :class:`str`
        The name of this option
    focused: :class:`bool`
        Whether the user is currently creating an input for this option. This is useful for :meth:`on_autocomplete`
    """

    __slots__: Tuple[str, ...] = (
        "data",
        "value",
        "type",
        "name",
        "focused"
    )

    def __init__(self, data) -> None:
        self.data: dict = data
        self.value: Union[str, int, float, bool] = data["value"]
        self.type: int = data["type"]
        self.name: str = data["name"]

        try:
            self.focused = data["focused"]
        except KeyError:
            self.focused = False

    def __repr__(self) -> str:
        return str(self.value)


class ApplicationCommandInteraction(Interaction):
    """Represents the interaction for all application commands.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
    application_command: Union[SlashApplicationSubcommand, BaseApplicationCommand]
        The application command that triggered the interaction.
    app_command_name: :class:`str`
        The name of the application command that triggered the interaction.
    app_command_id: :class:`int`
        The application command ID that triggered the interaction.
    options: List[SlashOptionData]
        The application command options that have been given a value.
    """

    __slots__: Tuple[str, ...] = (
        "application_command",
        "app_command_name",
        "app_command_id",
        "options",
    )

    def __init__(self, *, data: InteractionPayload, state: ConnectionState):
        super().__init__(data=data, state=state)

        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None

    def _from_data(self, data: InteractionPayload):
        super()._from_data(data=data)

        self.app_command_name: str = self.data["name"]  # type: ignore # self.data should be present here
        self.app_command_id: int = self.data["id"]  # type: ignore # self.data should be present here

        try:
            self.options: List[SlashOptionData] = self._get_application_options(self.data["options"])  # type: ignore # Data should be defined here
        except KeyError:
            self.options: List[SlashOptionData] = []

    def _set_application_command(
        self, app_cmd: Union[SlashApplicationSubcommand, BaseApplicationCommand]
    ):
        self.application_command = app_cmd

    def _get_application_options(self, data):
        options = data
        
        if len(options) == 0:
            # return empty list if no options exist
            return []

        # iterate through options to get inputs
        while "options" in options[0]:
            options = options[0]["options"]
            
            if len(options) == 0:
                # return empty list if no options exist 
                return []

        # If we are here, then the user provided an input for some options
        options_collection: List[SlashOptionData] = []

        for option in options:
            options_collection.append(SlashOptionData(option))

        return options_collection


class ApplicationAutocompleteInteraction(ApplicationCommandInteraction):
    """Represents the interaction for Autocompletes.

    This interaction inherits from :class:`ApplicationCommandInteraction`

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
    focused_option: :class:`SlashOptionData`
        The option the callback is for.
    """

    def __init__(self, *, data: InteractionPayload, state: ConnectionState):
        super().__init__(data=data, state=state)

        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None

    @property
    def focused_option(self) -> Optional[SlashOptionData]:
        for option in self.options:
            if option.focused:
                return option

        return None
