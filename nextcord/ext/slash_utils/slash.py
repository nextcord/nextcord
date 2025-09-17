# SPDX-License-Identifier: MIT

from typing import Callable, Dict, Iterable, Union

from nextcord import CallbackWrapper, SlashApplicationCommand, SlashApplicationSubcommand


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


def choices(
    **kwargs: Union[Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]],
) -> Callable[
    [Callable], Union[SlashApplicationCommand, SlashApplicationSubcommand, CallbackWrapper]
]:
    """
    Decorator that allows you to add choices to options of a slash command.

    Parameters
    ----------
    **kwargs: Union[Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]]
        Keyword arguments where the key is the option name and the value is a list of choices or a mapping of choice names to values.

    Example
    -------

    .. code-block:: python

        from nextcord.ext import slash_utils

        @slash_utils.choices(
            option1=["choice1", "choice2"],
            option2={"choice3": 3, "choice4": 4}
        )
        async def my_command(interaction: Interaction, option1: str, option2: int):
            pass

    """

    class ChoicesWrapper(CallbackWrapper):
        def modify(self, app_cmd: SlashApplicationCommand):
            option_names = {option.functional_name: option for option in app_cmd.options.values()}
            for given_name in kwargs:
                if option := option_names.get(given_name):
                    option.choices = kwargs[given_name]
                else:
                    raise ValueError(
                        f'{app_cmd.error_name} Could not find option "{given_name}" to add choices to.'
                    )

    def wrapper(func):
        return ChoicesWrapper(func)

    return wrapper
