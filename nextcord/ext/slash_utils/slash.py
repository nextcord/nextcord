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


def rename(
    **kwargs: str,
) -> Callable[
    [Callable], Union[SlashApplicationCommand, SlashApplicationSubcommand, CallbackWrapper]
]:
    class RenameWrapper(CallbackWrapper):
        def modify(self, app_cmd: SlashApplicationCommand):
            option_names = {option.functional_name: option for option in app_cmd.options.values()}
            for original_name, new_name in kwargs.items():
                if option := option_names.get(original_name):
                    # Remove the old name from the dict and add the new one
                    # We must do this because the dict is used to call the callback
                    option_names.pop(original_name)
                    option.name = new_name
                    option_names[new_name] = option
                else:
                    raise ValueError(
                        f'{app_cmd.error_name} Could not find option "{original_name}" to rename.'
                    )

            # Update the options dict with the new name(s)
            # We also need to sort it based on if the option is required or not -
            # this is because required options must be listed first in the dict
            app_cmd.options = {
                name: option
                for name, option in sorted(
                    option_names.items(),
                    key=lambda x: not x[1].required,
                )
            }

    def wrapper(func):
        return RenameWrapper(func)

    return wrapper
