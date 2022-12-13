# SPDX-License-Identifier: MIT

from enum import Enum  # , StrEnum

# While using the custom dpy/nc Enum would technically yield higher performance, these event enums should not be
#  constantly instantiated and garbage collected, so the extra speed should be negligible compared to the possible
#  usability concerns of using something that is called "Enum" but isn't actually the Enum from the Python library.


__all__ = (
    "ApplicationCommandEvents",
    "ClientEvents",
    "GatewayEvents",
    "StateEvents",
)


class ApplicationCommandEvents(Enum):
    APPLICATION_COMMAND_COMPLETION = "application_command_completion"
    APPLICATION_COMMAND_ERROR = "application_command_error"


class ClientEvents(Enum):
    DISCONNECT = "disconnect"
    """Dispatched when the client is disconnected from the Discord WS gateway, but may reconnect."""
    CLOSE = "close"
    """Dispatched when the client is specifically told to close."""


class GatewayEvents(Enum):
    SOCKET_RAW_RECEIVE = "socket_raw_receive"
    SOCKET_EVENT_TYPE = "socket_event_type"
    SOCKET_RAW_SEND = "socket_raw_send"


class StateEvents(Enum):
    # TODO: Go through all of these and double check with people that they are correct.
    #  Also I typed all of this out manually, misspellings are practically guaranteed.
    # https://discord.com/developers/docs/topics/gateway-events#receive-events
    AUTO_MODERATION_RULE_CREATE = "auto_moderation_rule_create"
    AUTO_MODERATION_RULE_UPDATE = "auto_moderation_rule_update"
    AUTO_MODERATION_RULE_DELETE = "auto_moderation_rule_delete"
    AUTO_MODERATION_ACTION_EXECUTION = "auto_moderation_action_execution"
    BULK_MESSAGE_DELETE = "bulk_message_delete"
    """Dispatched when the state parses the bulk deletion of messages and has at least 1 in cache."""
    CONNECT = "connect"
    """Dispatched when the state parses the initial Discord WS gateway connection data."""
    GUILD_AVAILABLE = "guild_available"
    """???"""  # TODO
    GUILD_JOIN = "guild_join"
    """???"""  # TODO
    MESSAGE_DELETE = "message_delete"
    """Dispatched when the state parses a message visible to the bot being deleted that the bot has in cache."""
    READY = "ready"
    """Dispatched when the state is ready and done caching all available guilds"""
    RESUMED = "resumed"
    """Dispatched when the state parses the resume of the connection to the Discord WS gateway."""
    RAW_MESSAGE_DELETE = "raw_message_delete"
    """Dispatched when the state parses a message visible to the bot being deleted."""
    RAW_BULK_MESSAGE_DELETE = "raw_bulk_message_delete"
    """Dispatched when the state parses the bulk deletion of messages."""
    RAW_MESSAGE_EDIT = "raw_message_edit"
    """Dispatched when the state parses the editing of a message."""
    MESSAGE_EDIT = "message_edit"
    """Dispatched when the state parses the editing of a message that it has in cache."""
    RAW_REACTION_ADD = "raw_reaction_add"
    """Dispatched when the state parses a reaction being added to a message visible to the bot."""
    RAW_REACTION_CLEAR = "raw_reaction_clear"
    """Dispatched when the state parses all reactions from a message being cleared."""
    RAW_REACTION_CLEAR_EMOJI = "raw_reaction_clear_emoji"
    """Dispatched when the state parses all instances of a specific emoji being removed from a message."""
    RAW_REACTION_REMOVE = "raw_reaction_remove"
    """Dispatched when the state parses a reaction being removed from a message."""
    REACTION_ADD = "reaction_add"
    """Dispatched when the state parses a reaction being added to a message visible to the bot and the reacting member
    is in the cache.
    """
    REACTION_CLEAR = "reaction_clear"
    """Dispatched when the state parses all reactions from a message it has in the cache being cleared."""
    REACTION_CLEAR_EMOJI = "reaction_clear_emoji"
    """Dispatched when the state parses all instances of a specific emoji being removed from a message in the cache."""
    REACTION_REMOVE = "reaction_remove"
    """Dispatched when the state parses a reaction being removed from a message in the cache and the unreacting user is
    also in the cache.
    """
    INTERACTION = "interaction"
    """Dispatched when the state parses an interaction for the bot."""
    USER_UPDATE = "user_update"
    """Dispatched when the state parses the a user being updated."""
    PRESENCE_UPDATE = "presence_update"
    """Dispatched when the state parses the presence of a user being updated."""
    INVITE_CREATE = "invite_create"
    """Dispatched when the state parses an invite for a guild being created."""
    INVITE_DELETE = "invite_delete"
    """Dispatched when the state parses an invite for a guild being deleted."""
    GUILD_CHANNEL_DELETE = "guild_channel_delete"
    """Dispatched when the state parses a channel in a guild being deleted."""
    PRIVATE_CHANNEL_UPDATE = "private_channel_update"
    """Dispatched when the state parses an update to a group DM. Since NC doesn't support user-bots, this should not
    be called unless Discord finally adds support for bots in group DMs.
    """
    GUILD_CHANNEL_UPDATE = "guild_channel_update"
    """Dispatched when the state parses an update to a guild channel."""
    GUILD_CHANNEL_CREATE = "guild_channel_update"
    """Dispatched when the state parses the creation of a channel in a guild."""
    PRIVATE_CHANNEL_PINS_UPDATE = "private_channel_pins_update"
    """Dispatched when the state parses a message being pinned in a DM."""
    GUILD_CHANNEL_PINS_UPDATE = "guild_channel_pins_update"
    """Dispatched when the state parses a message being pinned in a guild channel."""
    THREAD_JOIN = "thread_join"
    """Dispatched when the state parses the creation of a thread, or the bot being added to a private thread."""
    THREAD_UPDATE = "thread_update"
    """Dispatched when the state parses a thread being updated, such as the name being changed."""
    THREAD_DELETE = "thread_delete"
    """Dispatched when the state parses a thread being deleted."""
    THREAD_REMOVE = "thread_remove"
    """Dispatched when the state parses a data that shows the bot being removed from a thread."""
    # Not a real Discord event, appears to be split from "Thread Members Update"
    THREAD_MEMBER_JOIN = "thread_member_join"
    """Dispatched when the state parses a member joining a thread."""
    # Not a real Discord event, appears to be split from "Thread Members Update"
    THREAD_MEMBER_REMOVE = "thread_member_remove"
    """Dispatched when the state parses a member being removed from a thread."""
    # Not a real Discord event, appears to be split from "Thread Members Update"
    MEMBER_JOIN = "member_join"
    """Dispatched when the state parses a member joining a guild."""
    RAW_MEMBER_REMOVE = "raw_member_remove"
    """Dispatched when the state parses a member being removed from a guild."""
    MEMBER_REMOVE = "member_remove"
    """Dispatched when the state parses a member it has in cache being removed from a guild."""
    MEMBER_UPDATE = "member_update"
    """Dispatched when a guild member is updated and the old member is in cache."""
    GUILD_EMOJIS_UPDATE = "guild_emojis_update"
    GUILD_STICKERS_UPDATE = "guild_stickers_update"
    GUILD_UPDATE = "guild_update"
    GUILD_UNAVAILABLE = "guild_unavailable"
    GUILD_REMOVE = "guild_remove"
    MEMBER_BAN = "member_ban"
    MEMBER_UNBAN = "member_unban"
    GUILD_ROLE_CREATE = "guild_role_create"
    GUILD_ROLE_DELETE = "guild_role_delete"
    GUILD_ROLE_UPDATE = "guild_role_update"
    GUILD_INTEGRATIONS_UPDATE = "guild_integrations_update"
    INTEGRATION_CREATE = "integration_create"
    # This specifically requires a guild, not sure why it isn't GUILD_INTEGRATION_CREATE
    INTEGRATION_UPDATE = "integration_update"
    RAW_INTEGRATION_DELETE = "raw_integration_delete"
    WEBHOOKS_UPDATE = "webhooks_update"
    STAGE_INSTANCE_CREATE = "stage_instance_create"
    STAGE_INSTANCE_UPDATE = "stage_instance_update"
    STAGE_INSTANCE_DELETE = "stage_instance_delete"
    VOICE_STATE_UPDATE = "voice_state_update"
    RAW_TYPING = "raw_typing"
    TYPING = "typing"
    GUILD_SCHEDULED_EVENT_CREATE = "guild_scheduled_event_create"
    GUILD_SCHEDULED_EVENT_UPDATE = "guild_scheduled_event_update"
    GUILD_SCHEDULED_EVENT_DELETE = "guild_scheduled_event_delete"
    GUILD_SCHEDULED_EVENT_USER_ADD = "guild_scheduled_event_user_add"
    GUILD_SCHEDULED_EVENT_USER_REMOVE = "guild_scheduled_event_user_remove"

    SHARD_READY = "shard_ready"
    SHARD_CONNECT = "shard_connect"
    SHARD_RESUMED = "shard_resumed"
    MESSAGE = "message"


# TODO: State.py Line 1403 dispatches to the view store?
# TODO: State.py Line 1407 dispatches to the modal store?
