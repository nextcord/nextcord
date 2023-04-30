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
