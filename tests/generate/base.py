# SPDX-License-Identifier: MIT

import nextcord
from nextcord.ext import commands


class GenerateBase(commands.Cog):
    @nextcord.slash_command(name="test_gen")
    async def test_gen(self, interaction: nextcord.Interaction):
        await interaction.send("You shouldn't be able to see this!")
