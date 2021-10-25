import logging
from typing import Dict, Union

import nextcord


# consistency with the `nextcord` namespaced logging
log = logging.getLogger(__name__)

# default timeout parameter for menus in seconds
DEFAULT_TIMEOUT = 180.0

# type definition for the keyword-arguments that are
# used in both Message.edit and Messageable.send
SendKwargsType = Dict[str, Union[str, nextcord.Embed, nextcord.ui.View, None]]

# type definition for possible page formats
PageFormatType = Union[str, nextcord.Embed, SendKwargsType]

# type definition for emoji parameters
EmojiType = Union[str, nextcord.Emoji, nextcord.PartialEmoji]
