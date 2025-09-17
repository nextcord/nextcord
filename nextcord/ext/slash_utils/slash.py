# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Union

from nextcord import CallbackWrapper, SlashApplicationCommand, SlashApplicationSubcommand

if TYPE_CHECKING:
    from nextcord import SlashCommandOption


def describe(
    **kwargs: str,
) -> Callable[
    [Callable], Union[SlashApplicationCommand, SlashApplicationSubcommand, CallbackWrapper]
]:
    class DescribeWrapper(CallbackWrapper):
        def modify(self, app_cmd: SlashApplicationCommand):
            option_names = {option.functional_name: option for option in app_cmd.options.values()}
            for given_name in kwargs:
                if option := option_names.get(given_name):
                    option.description = kwargs[given_name]
                else:
                    raise ValueError(
                        f'{app_cmd.error_name} Could not find option "{given_name}" to describe.'
                    )

    def wrapper(func):
        return DescribeWrapper(func)

    return wrapper


def rename(
    **kwargs: str,
) -> Callable[
    [Callable], Union[SlashApplicationCommand, SlashApplicationSubcommand, CallbackWrapper]
]:
    """
    Decorator that allows you to rename options in a slash command.

    Parameters
    ----------
    **kwargs: str
        Keyword arguments where the key is the original option name and the value is the new name.

    Example
    -------

    .. code-block:: python

        from nextcord.ext import slash_utils

        @slash_utils.rename(_id='id') # users will see 'id' instead of '_id'
        async def my_command(interaction: Interaction, _id: str):
            pass
    """

    class RenameWrapper(CallbackWrapper):
        def modify(self, app_cmd: SlashApplicationCommand) -> None:
            new_options: dict[str, SlashCommandOption] = {}
            kwarg_temp = kwargs.copy()
            for original_name, option in app_cmd.options.copy().items():
                if new_name := kwarg_temp.get(original_name):
                    option.name = new_name
                    kwarg_temp.pop(original_name)
                else:
                    new_name = original_name

                new_options[new_name] = option

            app_cmd.options = new_options

            for name in kwarg_temp:
                raise ValueError(f'{app_cmd.error_name} could not find option "{name}" to rename.')

    def wrapper(func) -> RenameWrapper:
        return RenameWrapper(func)

    return wrapper
