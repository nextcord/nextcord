# SPDX-License-Identifier: MIT

import nextcord
from nextcord.ext import commands

from .. import test_components, utils
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
                await interaction.send(
                    f"```\n{[c.to_dict() for c in test_components.string_select_components]}\n```",
                    ephemeral=True,
                )
            case "response":
                data = await send_components(interaction, test_components.string_select_components)
                await interaction.send(f"```\n{data}\n```", ephemeral=True)
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)

    @components.subcommand(name="user_selects")
    async def user_selects(
        self,
        interaction: nextcord.Interaction,
        choice: str = nextcord.SlashOption(choices=["generated", "response"]),
    ):
        if utils.EnvVar.test_user is None:
            await interaction.send(
                "`TEST_USER` envvar must be set to run this command.", ephemeral=True
            )
            return

        match choice:
            case "generated":
                to_send = str([c.to_dict() for c in test_components.user_select_components])
                to_send = to_send.replace(str(utils.EnvVar.test_user), "utils.EnvVar.test_user")
                await interaction.send(f"```\n{to_send}\n```", ephemeral=True)
            case "response":
                data = await send_components(interaction, test_components.user_select_components)
                to_send = str(data)
                to_send = to_send.replace(
                    f"'{utils.EnvVar.test_user!s}'", 'f"{utils.EnvVar.test_user}"'
                )
                to_send = to_send.replace(str(utils.EnvVar.test_user), "utils.EnvVar.test_user")
                await interaction.send(f"```\n{to_send}\n```", ephemeral=True)
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)

    @components.subcommand(name="role_selects")
    async def role_selects(
        self,
        interaction: nextcord.Interaction,
        choice: str = nextcord.SlashOption(choices=["generated", "response"]),
    ):
        if utils.EnvVar.test_role is None:
            await interaction.send(
                "`TEST_ROLE` envvar must be set to run this command.", ephemeral=True
            )
            return

        match choice:
            case "generated":
                to_send = str([c.to_dict() for c in test_components.role_select_components])
                to_send = to_send.replace(str(utils.EnvVar.test_role), "utils.EnvVar.test_role")
                await interaction.send(f"```\n{to_send}\n```", ephemeral=True)
            case "response":
                data = await send_components(interaction, test_components.role_select_components)
                to_send = str(data)
                to_send = to_send.replace(
                    f"'{utils.EnvVar.test_role!s}'", 'f"{utils.EnvVar.test_role}"'
                )
                to_send = to_send.replace(str(utils.EnvVar.test_role), "utils.EnvVar.test_role")
                await interaction.send(f"```\n{to_send}\n```", ephemeral=True)
            case _:
                await interaction.send(f"Invalid choice `{choice}` provided!", ephemeral=True)
