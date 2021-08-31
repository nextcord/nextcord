from typing import Callable, Dict
from nextcord import Guild, Message
from .converter import Converter
from nextcord.ext.abc import ContextBase
from nextcord.ext.interactions import Bot
import nextcord
import re


class clean_content(Converter[str]):
    """Converts the argument to mention scrubbed version of
    said content.

    This behaves similarly to :attr:`~nextcord.Message.clean_content`.

    Attributes
    ------------
    fix_channel_mentions: :class:`bool`
        Whether to clean channel mentions.
    use_nicknames: :class:`bool`
        Whether to use nicknames when transforming mentions.
    escape_markdown: :class:`bool`
        Whether to also escape special markdown characters.
    remove_markdown: :class:`bool`
        Whether to also remove special markdown characters. This option is not supported with ``escape_markdown``

        .. versionadded:: 1.7
    """

    def __init__(
        self,
        *,
        fix_channel_mentions: bool = False,
        use_nicknames: bool = True,
        escape_markdown: bool = False,
        remove_markdown: bool = False,
    ) -> None:
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown
        self.remove_markdown = remove_markdown

    def resolve_member(self, id: int, msg: Message, guild: Guild) -> str:
        m = nextcord.utils.get(msg.mentions, id=id) or guild.get_member(id)
        name = m and (m.display_name if self.use_nicknames else m.name)
        return f'@{name}' if m else '@deleted-user'

    def resolve_role(self, id: int, msg: Message, guild: Guild) -> str:
        r = nextcord.utils.get(msg.role_mentions, id=id) or guild.get_role(id)
        return f'@{r.name}' if r else '@deleted-role'

    def resolve_user(self, id: int, msg: Message, bot: Bot) -> str:
        m = nextcord.utils.get(msg.mentions, id=id) or bot.get_user(id)
        return f'@{m.name}' if m else '@deleted-user'

    def resolve_channel(self, id: int, guild: Guild) -> str:
        c = guild.get_channel(id)
        return f'#{c.name}' if c else '#deleted-channel'

    async def convert(self, ctx: ContextBase, argument: str) -> str:
        msg = ctx.message

        if ctx.guild:
            resolve_member = lambda id: self.resolve_member(id, msg, ctx.guild)
            resolve_role = lambda id: self.resolve_role(id, msg, ctx.guild)
        else:
            resolve_member = lambda id: self.resolve_user(id, msg, ctx.bot)
            resolve_role = lambda _: '@deleted-role'

        if self.fix_channel_mentions and ctx.guild:
            resolve_channel = lambda id: self.resolve_channel(id, ctx.guild)
        else:
            resolve_channel = lambda id: f'<#{id}>'

        transforms: Dict[str, Callable[[int], str]] = {
            '@': resolve_member,
            '@!': resolve_member,
            '#': resolve_channel,
            '@&': resolve_role,
        }

        def repl(match: re.Match) -> str:
            key = match[1]
            id = int(match[2])
            return transforms[key](id)

        result = re.sub(r'<(@[!&]?|#)([0-9]{15,20})>', repl, argument)
        if self.escape_markdown:
            result = nextcord.utils.escape_markdown(result)
        elif self.remove_markdown:
            result = nextcord.utils.remove_markdown(result)

        # Completely ensure no mentions escape:
        return nextcord.utils.escape_mentions(result)