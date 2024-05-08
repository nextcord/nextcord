# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from .asset import Asset
from .enums import IntegrationType
from .permissions import Permissions

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.appinfo import (
        AppInfo as AppInfoPayload,
        ApplicationIntegrationTypeConfig as ApplicationIntegrationTypeConfigPayload,
        InstallParams as InstallParamsPayload,
        IntegrationTypesConfig as IntegrationTypesConfigPayload,
        PartialAppInfo as PartialAppInfoPayload,
        Team as TeamPayload,
    )
    from .user import User

__all__ = (
    "InstallParams",
    "ApplicationIntegrationTypeConfig",
    "AppInfo",
    "PartialAppInfo",
)


class InstallParams:
    """Represents the default scopes and permissions for an installation context.

    .. versionadded:: 3.0

    Attributes
    ----------
    scopes: List[:class:`str`]
        Scopes to add the application to this installation context with.
    permissions: :class:`Permissions`
        Permissions to request for the bot role.
    """

    __slots__ = (
        "scopes",
        "permissions",
    )

    def __init__(self, data: InstallParamsPayload) -> None:
        self.scopes: List[str] = data["scopes"]
        self.permissions: Permissions = Permissions(int(data["permissions"]))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} scopes={self.scopes} permissions={self.permissions!r}>"


class ApplicationIntegrationTypeConfig:
    """Represents the default scopes and permissions for an installation context.

    .. versionadded:: 3.0

    Attributes
    ----------
    oauth2_install_params: :class:`InstallParams`
        The scopes and permissions for this installation context.
    """

    __slots__ = ("oauth2_install_params",)

    def __init__(self, data: ApplicationIntegrationTypeConfigPayload) -> None:
        install_params = data.get("oauth2_install_params")
        self.oauth2_install_params: Optional[InstallParams] = (
            InstallParams(install_params) if install_params else None
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} oauth2_install_params={self.oauth2_install_params!r}>"


class AppInfo:
    """Represents the application info for the bot provided by Discord.


    Attributes
    ----------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    owner: :class:`User`
        The application owner.
    team: Optional[:class:`Team`]
        The application's team.

        .. versionadded:: 1.3

    description: :class:`str`
        The application description.
    bot_public: :class:`bool`
        Whether the bot can be invited by anyone or if it is locked
        to the application owner.
    bot_require_code_grant: :class:`bool`
        Whether the bot requires the completion of the full oauth2 code
        grant flow to join.
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.

    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.

        .. versionadded:: 1.3

    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.

        .. versionadded:: 2.0

    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.

        .. versionadded:: 2.0

    integration_types_config: Optional[Dict[:class:`IntegrationType`, :class:`ApplicationIntegrationTypeConfig`]]
        The default scopes and permissions for each supported installation context.

        .. versionadded:: 3.0
    """

    __slots__ = (
        "_state",
        "description",
        "id",
        "name",
        "rpc_origins",
        "bot_public",
        "bot_require_code_grant",
        "owner",
        "_icon",
        "verify_key",
        "team",
        "terms_of_service_url",
        "privacy_policy_url",
        "integration_types_config",
    )

    def __init__(self, state: ConnectionState, data: AppInfoPayload) -> None:
        from .team import Team

        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.description: str = data["description"]
        self._icon: Optional[str] = data["icon"]
        self.rpc_origins: List[str] = data["rpc_origins"]
        self.bot_public: bool = data["bot_public"]
        self.bot_require_code_grant: bool = data["bot_require_code_grant"]
        self.owner: User = state.create_user(data["owner"])

        team: Optional[TeamPayload] = data.get("team")
        self.team: Optional[Team] = Team(state, team) if team else None

        self.verify_key: str = data["verify_key"]

        self.terms_of_service_url: Optional[str] = data.get("terms_of_service_url")
        self.privacy_policy_url: Optional[str] = data.get("privacy_policy_url")

        integration_types_config: Optional[IntegrationTypesConfigPayload] = data.get(
            "integration_types_config"
        )
        self.integration_types_config: Optional[
            Dict[IntegrationType, ApplicationIntegrationTypeConfig]
        ]
        if integration_types_config:
            self.integration_types_config = {
                IntegrationType(int(integration_type)): ApplicationIntegrationTypeConfig(data)
                for integration_type, data in integration_types_config.items()
            }
        else:
            self.integration_types_config = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} name={self.name!r} "
            f"description={self.description!r} public={self.bot_public} "
            f"owner={self.owner!r}>"
        )

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path="app")


class PartialAppInfo:
    """Represents a partial AppInfo given by :func:`~nextcord.abc.GuildChannel.create_invite`

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    description: :class:`str`
        The application description.
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.
    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.
    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.
    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.
    """

    __slots__ = (
        "_state",
        "id",
        "name",
        "description",
        "rpc_origins",
        "verify_key",
        "terms_of_service_url",
        "privacy_policy_url",
        "_icon",
        "integration_types_config",
    )

    def __init__(self, *, state: ConnectionState, data: PartialAppInfoPayload) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self._icon: Optional[str] = data.get("icon")
        self.description: str = data["description"]
        self.rpc_origins: Optional[List[str]] = data.get("rpc_origins")
        self.verify_key: str = data["verify_key"]
        self.terms_of_service_url: Optional[str] = data.get("terms_of_service_url")
        self.privacy_policy_url: Optional[str] = data.get("privacy_policy_url")
        integration_types_config: Optional[IntegrationTypesConfigPayload] = data.get(
            "integration_types_config"
        )
        self.integration_types_config: Optional[
            Dict[IntegrationType, ApplicationIntegrationTypeConfig]
        ]
        if integration_types_config:
            self.integration_types_config = {
                IntegrationType(int(integration_type)): ApplicationIntegrationTypeConfig(data)
                for integration_type, data in integration_types_config.items()
            }
        else:
            self.integration_types_config = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>"

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path="app")
