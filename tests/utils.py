from __future__ import annotations

import os


class EnvironmentalVariables:
    online: bool = bool(os.getenv("ONLINE"))
    """If online tests should be ran."""
    bot_token: str | None = os.getenv("BOT_TOKEN")
    """Bot token to use for online tests."""
    test_channel: int | None = int(temp) if (temp := os.getenv("TEST_CHANNEL")) else None
    """Output text channel to use for online tests."""


EnvVar = EnvironmentalVariables
