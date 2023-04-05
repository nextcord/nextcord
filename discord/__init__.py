# SPDX-License-Identifier: MIT
"""Module to allow for backwards compatibility for existing code and extensions."""

from nextcord import *

__title__ = "nextcord"
__author__ = "Nextcord Developers & Rapptz"
__license__ = "MIT"
__copyright__ = "Copyright 2015-2021 Rapptz & 2021-present Nextcord Developers"
__version__ = "2.4.2"

__path__ = __import__("pkgutil").extend_path(__path__, __name__)
