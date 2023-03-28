from __future__ import annotations

import logging

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web import StreamResponse
from typing import Dict, Optional, Union

from .base import BaseEndpoint, BaseMiddleware

from ..enums import ApplicationRoleConnectionMetadataType, Locale
from ..types.role_connections import ApplicationRoleConnectionMetadata

_log = logging.getLogger(__name__)


__all__ = (
    "RoleConnVerifyEndpoint",
    "role_conn_metadata_generator",
)


ROLE_CONN_RESPONSE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔒</text></svg>">
    <title>{}</title>
  </head>
  <body>
	{}
  </body>
</html>
"""


class RoleConnVerifyEndpoint(BaseMiddleware, BaseEndpoint):
    def __init__(self):
        BaseMiddleware.__init__(self, route="/endpoint/verify-user")
        BaseEndpoint.__init__(self, [self.middleware])

    async def on_middleware_match(self, request: web.Request, handler: Handler) -> StreamResponse:
        return web.Response(
            body=ROLE_CONN_RESPONSE_TEMPLATE.format(
                "Nothing Accepted.", "<h1>👍 Nothing received but this works! 👍</h1><h1>Close Whenever</h1>"
            ),
            content_type="text/html",
        )


def role_conn_metadata_generator(
        value_type: Union[ApplicationRoleConnectionMetadataType, int],
        key: str,
        name: str,
        description: str,
        name_localizations: Optional[Dict[Union[str, Locale], str]] = None,
        description_localizations: Optional[Dict[Union[str, Locale], str]] = None,
) -> ApplicationRoleConnectionMetadata:
    ret = {
        "type": value_type.value if isinstance(value_type, ApplicationRoleConnectionMetadataType) else value_type,
        "key": key,
        "name": name,
        "description": description,
    }
    if name_localizations is not None:
        ret["name_localizations"] = {}
        for key, value in name_localizations.items():
            if isinstance(key, Locale):
                key = key.value

            ret["name_localizations"][key] = value

    if description_localizations is not None:
        ret["description_localizations"] = {}
        for key, value in name_localizations.items():
            if isinstance(key, Locale):
                key = key.value

            ret["description_localizations"][key] = value

    return ret
