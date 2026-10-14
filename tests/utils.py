# SPDX-License-Identifier: MIT

from __future__ import annotations

import os


class EnvironmentalVariables:
    online: bool = bool(int(temp)) if (temp := os.getenv("ONLINE")) else False
    """If online tests should be ran."""
    bot_token: str | None = os.getenv("BOT_TOKEN")
    """Bot token to use for online tests."""
    test_channel: int | None = int(temp) if (temp := os.getenv("TEST_CHANNEL")) else None
    """Output text channel ID to use for online tests."""
    test_guild: int | None = int(temp) if (temp := os.getenv("TEST_GUILD")) else None
    """Test guild ID to use for online tests, and if the test_gen slash commands should be bound to a guild."""
    test_role: int | None = int(temp) if (temp := os.getenv("TEST_ROLE")) else None
    """Test role ID to use for online tests."""
    test_user: int | None = int(temp) if (temp := os.getenv("TEST_USER")) else None
    """Test user ID to use for online tests."""


EnvVar = EnvironmentalVariables
