import discord
from discord.ext import commands

from os import getenv
from dotenv import load_dotenv
load_dotenv(override=True)

from json import load
with open("config.json") as file:
    config = load(file)

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or(config.get("prefix")), 
    case_insensitive=True
)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} with ID {bot.user.id}\nChecking ID...")
    if bot.user.id == int(getenv("TARGET_CLIENT_ID")):
        print("ID Check passed.")
    else:
        print("ID Check failed")
        ##TODO: MAKE BOT FAIL
        ##TODO: ADD OWNER CHECKS

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@commands.command()
async def servers(ctx):
    await ctx.send(f"{ctx.author.mention}, {len(bot.guilds)}!")
bot.add_command(servers)

bot.run(getenv("BOT_TOKEN"))