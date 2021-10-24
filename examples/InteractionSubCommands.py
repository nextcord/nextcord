import nextcord
from nextcord.ext import commands

client = commands.Bot()

@client.slash_command(guild_ids=[GUILD_ID]) # Making the command and limiting the guilds
async def main(interaction): #passing through interaction and indentifing the sub-command group name
    await interaction.response.send_message("This will never get called if this has subcommands.") # An Function Never Called


@main.subcommand() # Identifying The Sub-Command
async def sub1(interaction): # Making The Sub Command Name And Passing Through Interaction
    await interaction.response.send_message("This is subcommand 1!") # Sending A Response


@main.subcommand(name="sub2", description="This is subcommand 2 tricked out!") # Identifying The Sub-Command And Adding A Descripton
async def subcommand_two(interaction: Interaction, # passing in interaction
                        arg1: str = SlashOption(name="argument1", description="The first argument."), # Field 1
                        arg2: str = SlashOption(description="The second argument!", default=None)): # Field 2
    await interaction.response.send_message(f"This is subcommand 2 with arg1 {arg1} and arg2 {arg2}") # Responding With The Args/Fields


