"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


from nextcord.application_command import SlashApplicationCommand, SlashApplicationSubcommand, AppCmdCallbackWrapper
from typing import Union


def describe(**kwargs: str) -> Union[SlashApplicationCommand, SlashApplicationSubcommand, "DescribeWrapper"]:
    class DescribeWrapper(AppCmdCallbackWrapper):
        def modify(self, app_cmd: SlashApplicationCommand):
            option_names = {option.functional_name: option for option in app_cmd.options.values()}
            for given_name in kwargs:
                if option := option_names.get(given_name):
                    option.description = kwargs[given_name]
                else:
                    raise ValueError(f"{app_cmd.error_name} Could not find option \"{given_name}\" to describe.")

    def wrapper(func):
        return DescribeWrapper(func)
    return wrapper

