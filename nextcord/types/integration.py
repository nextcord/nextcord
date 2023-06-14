# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .snowflake import Snowflake
from .user import User


class IntegrationApplication(TypedDict):
    id: Snowflake
    name: str
    icon: Optional[str]
    description: str
    summary: str
    bot: NotRequired[User]


class IntegrationAccount(TypedDict):
    id: str
    name: str


IntegrationExpireBehavior = Literal[0, 1]


class PartialIntegration(TypedDict):
    id: Snowflake
    name: str
    type: IntegrationType
    account: IntegrationAccount


IntegrationType = Literal["twitch", "youtube", "discord"]


class BaseIntegration(PartialIntegration):
    enabled: bool
    syncing: bool
    synced_at: str
    user: User
    expire_behavior: IntegrationExpireBehavior
    expire_grace_period: int


class StreamIntegration(BaseIntegration):
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool


class BotIntegration(BaseIntegration):
    application: IntegrationApplication


Integration = Union[BaseIntegration, StreamIntegration, BotIntegration]
