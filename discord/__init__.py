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

Module to allow for backwards compatibility for existing code and extensions
"""

from nextcord import __title__, __author__, __license__, __copyright__, __version__, __path__
import logging
from typing import NamedTuple
from nextcord import VersionInfo, version_info
from nextcord.client import *
from nextcord.appinfo import *
from nextcord.user import *
from nextcord.emoji import *
from nextcord.partial_emoji import *
from nextcord.activity import *
from nextcord.channel import *
from nextcord.guild import *
from nextcord.flags import *
from nextcord.member import *
from nextcord.message import *
from nextcord.asset import *
from nextcord.errors import *
from nextcord.permissions import *
from nextcord.role import *
from nextcord.file import *
from nextcord.colour import *
from nextcord.integrations import *
from nextcord.invite import *
from nextcord.template import *
from nextcord.widget import *
from nextcord.object import *
from nextcord.reaction import *
from nextcord import utils, opus, abc, ui
from nextcord.enums import *
from nextcord.embeds import *
from nextcord.mentions import *
from nextcord.shard import *
from nextcord.player import *
from nextcord.webhook import *
from nextcord.voice_client import *
from nextcord.audit_logs import *
from nextcord.raw_models import *
from nextcord.team import *
from nextcord.sticker import *
from nextcord.stage_instance import *
from nextcord.interactions import *
from nextcord.components import *
from nextcord.threads import *

__title__ = 'discord'
__author__ = 'tag-epic & Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-present Rapptz'
__version__ = '2.0.0a1'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)