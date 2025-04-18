"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-2021 Rapptz
:copyright: (c) 2021-present Nextcord Developers
:license: MIT, see LICENSE for more details.
"""

__title__ = "nextcord"
__author__ = "Nextcord Developers & Rapptz"
__license__ = "MIT"
__copyright__ = "Copyright 2015-2021 Rapptz & 2021-present Nextcord Developers"
# Placeholder, modified by dynamic-versioning.
__version__ = "0.0.0"

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import logging
from typing import Literal, NamedTuple

from . import abc, opus, ui, utils
from .activity import *
from .appinfo import *
from .application_command import *
from .asset import *
from .audit_logs import *
from .auto_moderation import *
from .bans import *
from .channel import *
from .client import *
from .colour import *
from .components import *
from .embeds import *
from .emoji import *
from .entitlement import *
from .enums import *
from .errors import *
from .file import *
from .flags import *
from .guild import *
from .guild_preview import *
from .integrations import *
from .interactions import *
from .invite import *
from .member import *
from .mentions import *
from .message import *
from .object import *
from .partial_emoji import *
from .permissions import *
from .player import *
from .raw_models import *
from .reaction import *
from .role import *
from .role_connections import *
from .scheduled_events import *
from .shard import *
from .stage_instance import *
from .sticker import *
from .team import *
from .template import *
from .threads import *
from .user import *
from .voice_client import *
from .webhook import *
from .widget import *


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int
    metadata: str


# Placeholder, modified by dynamic-versioning.
version_info: VersionInfo = VersionInfo(0, 0, 0, "final", 0, "")

logging.getLogger(__name__).addHandler(logging.NullHandler())
