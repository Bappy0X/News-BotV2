import discord
from discord.ext import commands

from os import getenv
from dotenv import load_dotenv
load_dotenv(override=True)

from json import load
with open("config.json") as file:
    config = load(file)

config["prefix"] = getenv("PREFIX")
config["embed_colour"] = int(getenv("EMBED_COLOUR"))

bot = commands.AutoShardedBot(
    command_prefix = commands.when_mentioned_or(getenv("PREFIX")), 
    case_insensitive = True
)
bot.remove_command("help")
bot._config = config

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

@commands.command()
async def shutdown(ctx):
    await ctx.send(f"{ctx.author.mention}, Shutting down!")
    await bot.close()
bot.add_command(shutdown)

if __name__ == "__main__":
    bot.load_extension("extensions.feeds")
    bot.run(getenv("BOT_TOKEN"))