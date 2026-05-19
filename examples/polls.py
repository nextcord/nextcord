from nextcord import Intents, PollCreateRequest, PollMedia
from nextcord.ext import commands

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.command()
async def send_poll(ctx: commands.Context):
    poll = PollCreateRequest(
        question=PollMedia(text="What is your favourite subject?"),
        allow_multiselect=True,
        duration=24,
    )

    # 📖
    poll.add_answer("Literature", "\U0001f4d6")
    # 🔢
    poll.add_answer("Maths", "\U0001f522")
    # 🧪
    poll.add_answer("Science", "\U0001f9ea")
    await ctx.send(poll=poll)


bot.run("token")
