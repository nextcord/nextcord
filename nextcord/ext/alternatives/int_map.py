"""An experiment that enables ``__int__`` on certain objects
to return the ``id`` attribute.
"""

import nextcord


_int = lambda self: self.id

nextcord.AppInfo.__int__ = _int
nextcord.Attachment.__int__ = _int
nextcord.AuditLogEntry.__int__ = _int
nextcord.emoji._EmojiTag.__int__ = _int
nextcord.mixins.Hashable.__int__ = _int
nextcord.Member.__int__ = _int
nextcord.Message.__int__ = _int
nextcord.Reaction.__int__ = _int
nextcord.Team.__int__ = _int
nextcord.Webhook.__int__ = _int
