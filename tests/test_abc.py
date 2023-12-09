# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

import nextcord
from nextcord import abc


@pytest.mark.asyncio()
class TestGuildChannel:
    @pytest.fixture()
    def channel(self):
        channel = mock.Mock(
            abc.GuildChannel,
            id=1,
            category_id=22,
            position=1,
            _state=mock.Mock(http=mock.AsyncMock()),
            guild=mock.Mock(),
        )
        category = mock.Mock(_overwrites=[mock.Mock() for _ in range(2)])
        channel.guild.get_channel.return_value = category
        return channel

    async def test_move(self, channel):
        channel.guild.channels = [channel]
        res = await abc.GuildChannel._move(channel, position=2, parent_id=5, reason="h")
        assert res is None
        channel._state.http.bulk_channel_update.assert_awaited_once_with(
            channel.guild.id,
            [{"id": 1, "position": 0, "parent_id": 5, "lock_permissions": False}],
            reason="h",
        )

    async def test_move_called(self, channel):
        res = await abc.GuildChannel._edit(
            channel,
            options={"position": 3, "category": nextcord.Object(5), "sync_permissions": True},
            reason="h",
        )
        assert res is None
        channel._move.assert_awaited_once_with(3, parent_id=5, lock_permissions=True, reason="h")
        channel._state.http.edit_channel.assert_not_called()

    async def test_edit_and_move(self, channel):
        role = mock.Mock(nextcord.Role)
        member = mock.Mock(nextcord.Member)
        res = await abc.GuildChannel._edit(
            channel,
            {
                "category": nextcord.Object(42),
                "slowmode_delay": 5,
                "rtc_region": nextcord.VoiceRegion.southafrica,
                "video_quality_mode": nextcord.VideoQualityMode.full,
                "default_sort_order": nextcord.SortOrderType.creation_date,
                "default_forum_layout": nextcord.ForumLayoutType.gallery,
                "sync_permissions": True,
                "position": 5,
                "overwrites": {
                    member: nextcord.PermissionOverwrite(send_messages=True),
                    role: nextcord.PermissionOverwrite(administrator=True),
                },
                "default_thread_slowmode_delay": 10,
                "default_reaction": "<:tomsnotlikethis:1054064157726621796>",
                "type": nextcord.ChannelType.news,
                "available_tags": [nextcord.ForumTag(id=12, name="bad", moderated=True)],
            },
            reason="h",
        )
        assert res is channel._state.http.edit_channel.return_value
        channel._state.http.edit_channel.assert_awaited_once_with(
            channel.id,
            reason="h",
            type=5,
            rate_limit_per_user=5,
            rtc_region="southafrica",
            video_quality_mode=2,
            default_sort_order=1,
            default_forum_layout=2,
            permission_overwrites=[
                {"allow": 2048, "deny": 0, "id": member.id, "type": 1},
                {"allow": 8, "deny": 0, "id": role.id, "type": 0},
            ],
            default_thread_rate_limit_per_user=10,
            default_reaction_emoji={
                "emoji_id": 1054064157726621796,
            },
            available_tags=[{"id": 12, "name": "bad", "moderated": True}],
        )
        channel._move.assert_awaited_once_with(5, parent_id=42, lock_permissions=True, reason="h")

    async def test_edit__sync_permissions(self, channel):
        res = await abc.GuildChannel._edit(channel, {"sync_permissions": True}, reason="h")
        assert res is channel._state.http.edit_channel.return_value
        channel._state.http.edit_channel.assert_awaited_once_with(
            channel.id,
            reason="h",
            permission_overwrites=[
                o._asdict() for o in channel.guild.get_channel.return_value._overwrites
            ],
        )
        channel._move.assert_not_called()

    async def test_move__no_cache(self, channel):
        channel.guild.channels = []
        res = await abc.GuildChannel._move(channel, position=2, parent_id=5, reason="h")
        assert res is None
        assert channel._state.http.bulk_channel_update.called is False

    async def test_edit__change_category(self, channel):
        res = await abc.GuildChannel._edit(
            channel, {"sync_permissions": True, "category": nextcord.Object(5)}, reason="h"
        )
        assert res is channel._state.http.edit_channel.return_value
        channel._state.http.edit_channel.assert_awaited_once_with(
            channel.id,
            reason="h",
            permission_overwrites=[
                o._asdict() for o in channel.guild.get_channel.return_value._overwrites
            ],
            parent_id=5,
        )
