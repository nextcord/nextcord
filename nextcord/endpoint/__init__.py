from __future__ import annotations

import logging

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web import StreamResponse

from ..enums import OAuth2Scopes
from .base import BaseEndpoint
from .oauth import OAuth2Endpoint, oauth_url_request_generator
from .role_conn_verify import RoleConnVerifyEndpoint, role_conn_metadata_generator

_log = logging.getLogger(__name__)


__all__ = (
    "oauth_url_request_generator",
    "OAuth2Endpoint",
    "role_conn_metadata_generator",
    "RoleConnVerifyEndpoint",
    "UnifiedEndpoint",
)


class UnifiedEndpoint(BaseEndpoint):
    def __init__(
        self,
        oauth2: bool = True,
        role_conn: bool = True,
    ) -> None:
        middles = []
        self.oauth2 = OAuth2Endpoint()
        if oauth2:
            middles.append(self.oauth2.middleware())

        self.role_conn = RoleConnVerifyEndpoint()
        if role_conn:
            middles.append(self.role_conn.middleware())

        # if oauth2 and role_conn:
        #     self.role_conn.on_middleware_match = self.role_conn_override

        super().__init__(middles)
