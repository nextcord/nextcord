import typing

from nextcord.flags import fill_with_flags, flag_value, BaseFlags

__all__ = (
    'EventFlags',
)

class _auto_value:
    _CURR_VALUE = 0

    def __rlshift__(self, val) -> int:
        ret = val << self._CURR_VALUE
        self._CURR_VALUE += 1
        return ret

    def reset(self) -> None:
        self._CURR_VALUE = 0

_GLOBAL_AUTO_VALUE = _auto_value()


def auto(doc=None, *, last=False) -> flag_value:
    _bit = 1 << _GLOBAL_AUTO_VALUE
    if last:
        _GLOBAL_AUTO_VALUE.reset()

    def pred(self) -> int:
        return _bit
    
    pred.__doc__ = doc
    return flag_value(pred)

class propmethod:
    def __init__(self, func):
        self._func = func
        self._flag = None
    
    def __get__(self, instance, owner):
        if instance is None:
            def pred():
                cls = owner
                _self = cls.__new__(cls)
                _self.value = self._func(cls)
                return _self
            return pred

        self._flag = flag_value(lambda n: self._func(instance))
        return self._flag.__get__(instance, owner)
        
    def __set__(self, instance, value):
        if instance is not None:
            if self._flag is None:
                self._flag = flag_value(lambda n: self._func(instance))
            self._flag.__set__(instance, value)
        else:
            return


class BaseScienceFlags(BaseFlags):
    @propmethod
    def all(cls):
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        return (1 << bits) - 1
    
    @propmethod
    def none(cls):
        return cls.DEFAULT_VALUE


@fill_with_flags()
class EventFlags(BaseScienceFlags):
    @propmethod
    def guilds(cls):
        return 127

    guild_join = auto('The on_guild_join event')
    guild_remove = auto('The on_guild_remove event')
    guild_available = auto('The on_guild_available event')
    guild_unavailable = auto('The on_guild_unavailable event')
    guild_channel_update = auto('The on_guild_channel_update event')
    guild_channel_create = auto('The on_guild_channel_delete event')
    guild_channel_delete = auto('The on_guild_channel_pins_update event')

    @propmethod
    def members(cls):
        return 896
    
    member_join = auto('The on_member_join event')
    member_remove = auto('The on_member_remove event')
    member_update = auto('The on_member_update event')

    @propmethod
    def bans(cls):
        return 3072
    
    member_ban = auto('The on_member_ban event')
    member_unban = auto('The on_member_unban event')

    @propmethod
    def emojis(cls):
        return 4096
    
    guild_emojis_update = auto('The on_guild_emojis_update event')

    @propmethod
    def integrations(cls):
        return 8192

    guild_integrations_update = auto('The on_guild_integrations_update event')

    @propmethod
    def webhooks(cls):
        return 16384
    
    webhooks_update = auto('The on_webhooks_update event')

    @propmethod
    def invites(cls):
        return 98304
    
    invite_create = auto('The on_invite_create event')
    invite_delete = auto('The on_invite_delete event')

    @propmethod
    def voice_states(cls):
        return 131072
    
    voice_state_update = auto('The on_voice_state_update event')

    @propmethod
    def presences(cls):
        return 262144
    
    presence_update = auto('The on_member_update event')

    @propmethod
    def messages(cls):
        return 7864320
    
    message = auto('The on_message event')
    message_update = auto('The on_message_update event')
    message_delete = auto('The on_message_delete event')
    private_channel_create = auto('The on_private_channel_create event')

    @propmethod
    def reactions(cls):
        return 58720256
    
    reaction_add = auto('The on_reaction_add event')
    reaction_remove = auto('The on_reaction_remove event')
    reaction_clear = auto('The on_reaction_clear event')
    
    typing = auto('The on_typing event', last=True)


@fill_with_flags()
class OpFlags(BaseScienceFlags):
    DISPATCH = auto('An event sent to the Client (ie. READY).')
    HEARTBEAT = auto('To keep the connection alive.')
    IDENTIFY = auto('When a new session is started.')
    PRESENCE = auto('When you update your presence.')
    VOICE_STATE = auto('When a new connection is started to a voice guild.')
    VOICE_PING = auto('Checks the ping time to a voice guild.')
    RESUME = auto('When an existing connection is resumed.')
    RECONNECT = auto('When the client is told to reconnect.')
    REQUEST_MEMBERS = auto('When you ask for a full member list of a guild.')
    INVALIDATE_SESSION = auto('When the client is told to invalidate the session and re-IDENTIFY.')
    HELLO = auto('When the client is told the heartbeat interval.')
    HEARTBEAT_ACK = auto('When the heartbeat received is confirmed.')
    GUILD_SYNC = auto('When a guild sync is requested.', last=True)
