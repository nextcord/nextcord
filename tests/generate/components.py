# SPDX-License-Identifier: MIT

import nextcord
from nextcord.ext import commands

from .. import test_components
from .base import GenerateBase


async def send_components(interaction: nextcord.Interaction, components: list[nextcord.Component]):
    flags = nextcord.MessageFlags()
    flags.is_components_v2 = True
    data = await interaction.client.http.send_message(
        interaction.channel_id,
        None,
        components=[c.to_dict() for c in components],
        flags=flags.value,
    )
    return data["components"]


class GenerateComponents(commands.Cog):
    @GenerateBase.test_gen.subcommand(name="components")
    async def components(self, interaction: nextcord.Interaction):
        await interaction.send("You shouldn't be able to see this!")

    @components.subcommand(name="buttons")
    async def buttons(
        self,
        interaction: nextcord.Interaction,
        choice: str = nextcord.SlashOption(choices=["generated", "response"]),
    ):
        match choice:
            case "generated":
                await interaction.send(
                    f"```\n{[c.to_dict() for c in test_components.button_components]}\n```",
                    ephemeral=True,
                )
            case "response":
                data = await send_components(interaction, test_components.button_components)
                await interaction.send(f"```\n{data}\n```", ephemeral=True)
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)

    @components.subcommand(name="string_select_options")
    async def string_select_options(
        self,
        interaction: nextcord.Interaction,
        choice: str = nextcord.SlashOption(choices=["generated", "response"]),
    ):
        match choice:
            case "generated":
                await interaction.send(
                    f"```\n{[c.to_dict() for c in test_components.select_option_components]}\n```",
                    ephemeral=True,
                )
            case "response":
                comps = [
                    nextcord.ActionRow(
                        [nextcord.StringSelect(options=test_components.select_option_components)]
                    )
                ]
                data = await send_components(interaction, comps)
                await interaction.send(
                    f"```\n{data[0]["components"][0]["options"]}\n```", ephemeral=True
                )
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)

    @components.subcommand(name="string_selects")
    async def string_selects(
        self,
        interaction: nextcord.Interaction,
        choice: str = nextcord.SlashOption(choices=["generated", "response"]),
    ):
        match choice:
            case "generated":
                pass
            case "response":
                pass
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)
