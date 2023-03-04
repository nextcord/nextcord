# SPDX-License-Identifier: MIT

from typing import Callable, Union

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
