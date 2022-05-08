import discord
from discord.ext import commands
import secrets


# Set Up Bot (Globally I guess)
intents = discord.Intents(messages=True, guilds=True)
try: 
    intents.members = True
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
except:
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
# End Bot Setup


@bot.command(pass_context=True)
async def ping(ctx):
    await ctx.send("pong")

bot.run(secrets.TOKEN)
