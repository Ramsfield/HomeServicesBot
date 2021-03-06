import discord
import qbittorrentapi
import threading
import re
from discord.ext import commands
from time import sleep
import asyncio
import subprocess

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

def timeToString(t):
    hours = t // (60 * 60)
    minutes = t // (60) - (hours * 60)
    seconds = t - (hours * 60 * 60) - (minutes * 60)
    hstring = f"{hours} hours" if hours != 0 else ""
    mstring = f"{minutes} minutes" if minutes != 0 else ""
    sstring = f"{seconds} seconds" if seconds != 0 else ""
    return f"{hstring} {mstring} {sstring}"

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
        return await ctx.send(f"Upload speeds slowed for the next {timeToString(current_sleep_time)}")
    else:
        return await ctx.send(f"Upload speeds are manually slowed down")

@bot.command(pass_context=True)
async def addtime(ctx):
    """
    Will add 30 minutes to the slowdown timer up to 2 hours
    """
    global sleep_time
    global current_sleep_time
    time_to_add = sleep_time - current_sleep_time
    time_to_add = time_to_add if time_to_add < (30 * 60) else 30 * 60
    current_sleep_time += time_to_add
    addedString = timeToString(time_to_add)
    if addedString == "":
        addedString = "no time"
    return await ctx.send(f"Added {timeToString(time_to_add)}, timer now at {timeToString(current_sleep_time)}")

@bot.command(pass_context=True)
async def speedtest(ctx):
    """
    Performs a speed test to determine the up and down speed of the server
    """
    ps = subprocess.run(['which', 'speedtest'], stdout=subprocess.PIPE)
    if(ps.returncode != 0):
        return await ctx.send("Speedtest not in path. Exiting")
    program = ps.stdout.decode('utf-8').rstrip()
    await ctx.send("Beginning speed test")
    ps = subprocess.run([program], stdout=subprocess.PIPE)
    output = ps.stdout.decode('utf-8')
    down = "0"
    up = "0"
    dstring = "Download:\s+[\d.]+\s.bps"
    ustring = "Upload:\s+[\d.]+\s.bps"
    down = re.search(dstring, output)[0]
    up = re.search(ustring, output)[0]
    return await ctx.send(f"{down}\n{up}")

bot.run(secrets.TOKEN)
