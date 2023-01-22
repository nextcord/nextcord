from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from .base import Interaction

__all__ = (
    "ApplicationCommandInteraction",
    "ApplicationAutocompleteInteraction"
)

if TYPE_CHECKING:
    from ..application_command import BaseApplicationCommand, SlashApplicationSubcommand
    from ..types.interactions import Interaction as InteractionPayload, InteractionData
    from ..state import ConnectionState
    from ..application_command import SlashOptionData


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
        "options"
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
        options_collection: List[SlashOptionData] = []

        for option in data:
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

    # __slots__: Tuple[str, ...] = ("focused_option", )

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