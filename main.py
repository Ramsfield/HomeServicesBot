import discord
import qbittorrentapi
import threading
from discord.ext import commands
from time import sleep
import asyncio

import secrets

# Set Up Bot (Globally I guess)
intents = discord.Intents(messages=True, guilds=True)
try: 
    intents.members = True
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
except:
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
# End Bot Setup

# Get Qbit client
qbit = secrets.qbitClient()
try:
    qbit.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    print(e)
    exit(1)
# End Qbit client setup

hours_to_sleep = 2
sleep_time =  hours_to_sleep * 60 * 60
current_sleep_time = 0
isSlow = False
slowThread = threading.Thread()
loop = asyncio.get_event_loop()

def slowdownThread(ctx):
    global qbit
    global current_sleep_time
    global isSlow
    global loop
    while current_sleep_time > 0:
        ttS = 10
        sleep(ttS)
        current_sleep_time -= ttS
        slowed = qbit.transfer_upload_limit() > 0
        if not slowed:
            isSlow = False
            loop.create_task(ctx.send("Speed limits no longer slowed by outside factors. Ending slowdown"))
            return
    qbit.transfer_set_upload_limit(0)
    isSlow = False
    slowed = qbit.transfer_upload_limit() > 0
    if slowed:
        loop.create_task(ctx.send("Unable to speed rates back up."))
        return
    loop.create_task(ctx.send("Upload speeds back to normal rates."))
    return

@bot.command(pass_context=True, hidden=True)
async def ping(ctx):
    await ctx.send("pong")

@bot.command(pass_context=True)
async def slowdown(ctx):
    """
    Will slow down uploads for 2 hours
    Hopefully freeing up enough bandwidth to stream easily
    """
    global qbit
    global hours_to_sleep
    global sleep_time
    global current_sleep_time
    global isSlow
    global slowThread
    slowed = qbit.transfer_upload_limit() > 0
    if slowed:
        return await ctx.send("Uploads already slowed")
    qbit.transfer_set_upload_limit(10240)
    slowed = qbit.transfer_upload_limit() > 0
    if not slowed:
        return await ctx.send("Something went wrong")
    await ctx.send(f"Uploads slowed for the next {hours_to_sleep} hours.")
    current_sleep_time = sleep_time
    isSlow = True
    slowThread = threading.Thread(target=slowdownThread, args=([ctx]))
    slowThread.start()

@bot.command(pass_context=True)
async def speedup(ctx):
    """
    Speeds uploads back up, cancelling previous slowdowns
    """
    global qbit
    slowed = qbit.transfer_upload_limit() > 0
    if not slowed:
        return await ctx.send("Upload speeds currently at max")
    qbit.transfer_set_upload_limit(0)
    slowed = qbit.transfer_upload_limit() > 0
    if not slowed:
        return await ctx.send("Upload speeds now at max")
    else:
        return await ctx.send("Something went wrong")

@bot.command(pass_context=True)
async def isslow(ctx):
    """
    Determines if a slowdown is in effect
    """
    global qbit
    global isSlow
    global current_sleep_time
    slowed = qbit.transfer_upload_limit() > 0
    if not slowed:
        return await ctx.send("Upload speeds currently at max")
    elif isSlow:
        hours = current_sleep_time // (60 * 60)
        minutes = current_sleep_time // (60) - (hours * 60)
        seconds = current_sleep_time - (hours * 60 * 60) - (minutes * 60)
        hstring = f"{hours} hours" if hours != 0 else ""
        mstring = f"{minutes} minutes" if minutes != 0 else ""
        sstring = f"{seconds} seconds" if seconds != 0 else ""
        return await ctx.send(f"Upload speeds slowed for the next {hstring} {mstring} {sstring}")
    else:
        return await ctx.send(f"Upload speeds are manually slowed down")

bot.run(secrets.TOKEN)
