# SPDX-License-Identifier: MIT

import nextcord
from nextcord.ext import commands

from .base import GenerateBase

button_components = [
    nextcord.ActionRow(
        [
            nextcord.Button.as_primary(
                label="Primary1", component_id=11, custom_id="test_button_11"
            ),  # Test basic label.
            nextcord.Button.as_primary(
                emoji="⚠️", component_id=12, custom_id="test_button_12"
            ),  # Test basic string emoji.
            nextcord.Button.as_primary(
                label="Primary3", emoji="⚠️", component_id=13, custom_id="test_button_13"
            ),  # Test label + emoji.
            nextcord.Button.as_primary(
                label="Primary4", disabled=True, component_id=14, custom_id="test_button_14"
            ),  # Test Disabled = True.
            nextcord.Button.as_primary(
                label="Primary5",
                disabled=False,
                component_id=15,
                custom_id="test_button_15",
            ),  # Test Disabled = False.
        ],
        component_id=1,
    ),
    nextcord.ActionRow(
        [
            nextcord.Button.as_secondary(
                label="Secondary", component_id=21, custom_id="test_button_21"
            ),
            nextcord.Button.as_success(
                label="Success", component_id=22, custom_id="test_button_22"
            ),
            nextcord.Button.as_danger(label="Danger", component_id=23, custom_id="test_button_23"),
        ],
        component_id=2,
    ),
    nextcord.ActionRow(
        [
            nextcord.Button.as_link(
                "https://docs.discord.com/developers/components/reference#button",
                label="Link1",
                component_id=31,
            ),
        ],
        component_id=3,
    ),
]


class GenerateComponents(commands.Cog):
    @GenerateBase.test_gen.subcommand(name="components")
    async def components(self, interaction: nextcord.Interaction):
        await interaction.send("You shouldn't be able to see this!")

    @components.subcommand(name="buttons_generated")
    async def buttons_generated(self, interaction: nextcord.Interaction):
        await interaction.send(
            f"```\n{[c.to_dict() for c in button_components]}\n```", ephemeral=True
        )

    @components.subcommand(name="buttons_response")
    async def buttons_response(self, interaction: nextcord.Interaction):
        flags = nextcord.MessageFlags()
        flags.is_components_v2 = True
        data = await interaction.client.http.send_message(
            interaction.channel_id,
            None,
            components=[c.to_dict() for c in button_components],
            flags=flags.value,
        )
        await interaction.send(f"```\n{data["components"]}\n```", ephemeral=True)
