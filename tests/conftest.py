# SPDX-License-Identifier: MIT

import asyncio

import pytest

from nextcord.errors import HTTPException
from nextcord.http import HTTPClient
from tests.utils import EnvVar


@pytest.fixture(scope="session")
async def http_session():
    http_client = HTTPClient(
        dispatch=lambda event, *_: None, default_auth=f"Bot {EnvVar.bot_token}"  # noqa: ARG005
    )
    yield http_client
    await http_client.close()


async def check_valid_token() -> bool | str:
    http_client = HTTPClient(dispatch=lambda event, *_: None)  # noqa: ARG005
    try:
        await http_client.get_current_user(auth=f"Bot {EnvVar.bot_token}")
    except HTTPException as exc:
        if exc.status == 401:
            return "Improper token has been passed."
        return f"Exception status code {exc.status}"
    else:
        return True


if EnvVar.online:
    if EnvVar.bot_token is None:
        pytest.exit("Online is enabled, but BOT_TOKEN isn't passed.")
    elif EnvVar.test_channel is None:
        pytest.exit("Online is enabled, but TEST_CHANNEL isn't passed.")
        # TODO: Add test channel tests to make sure it's a normal text channel?
    else:
        ret = asyncio.run(check_valid_token())
        if ret is not True:
            pytest.exit(f"Valid token check failed: {ret}")
