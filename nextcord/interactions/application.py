# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from .base import Interaction

__all__ = ("ApplicationCommandInteraction", "ApplicationAutocompleteInteraction")

if TYPE_CHECKING:
    from ..application_command import (
        BaseApplicationCommand,
        SlashApplicationSubcommand,
        SlashOptionData,
    )
    from ..state import ConnectionState
    from ..types.interactions import (
        ApplicationAutocompleteInteraction as ApplicationAutocompletePayload,
        ApplicationCommandInteraction as ApplicationCommandPayload,
    )


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

    def __init__(self, *, data: ApplicationCommandPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None

    def _from_data(self, data: ApplicationCommandPayload) -> None:
        super()._from_data(data=data)

        self.app_command_name: str = self.data["name"]  # type: ignore # self.data should be present here
        self.app_command_id: int = self.data["id"]  # type: ignore # self.data should be present here

        try:
            self.options: List[SlashOptionData] = self._get_application_options(self.data["options"])  # type: ignore # Data should be defined here
        except KeyError:
            self.options: List[SlashOptionData] = []

    def _set_application_command(
        self, app_cmd: Union[SlashApplicationSubcommand, BaseApplicationCommand]
    ) -> None:
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

        from ..application_command import (  # Importing here due to circular import issues
            SlashOptionData,
        )

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

    def __init__(self, *, data: ApplicationAutocompletePayload, state: ConnectionState) -> None:
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
