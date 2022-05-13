"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
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

from .core import (
    application_command_after_invoke,
    application_command_before_invoke,
    bot_has_any_role,
    bot_has_guild_permissions,
    bot_has_permissions,
    bot_has_role,
    check,
    check_any,
    dm_only,
    guild_only,
    has_any_role,
    has_guild_permissions,
    has_permissions,
    has_role,
    is_nsfw,
    is_owner,
)
from .errors import (
    ApplicationBotMissingAnyRole,
    ApplicationBotMissingPermissions,
    ApplicationBotMissingRole,
    ApplicationCheckAnyFailure,
    ApplicationCheckForBotOnly,
    ApplicationMissingAnyRole,
    ApplicationMissingPermissions,
    ApplicationMissingRole,
    ApplicationNoPrivateMessage,
    ApplicationNotOwner,
    ApplicationNSFWChannelRequired,
    ApplicationPrivateMessageOnly,
)
