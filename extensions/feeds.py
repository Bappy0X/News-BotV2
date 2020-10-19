import aiohttp, feedparser
from asyncio import sleep, get_event_loop
from datetime import datetime
from time import mktime
import aiosqlite

import discord
from discord.ext import commands

firstRun = True
feed = []

class Source:
    def __init__(self, data):
        self.name = data[0]
        self.short = data[1]
        self.url = data[2]
        self.icon = data[3]
        self.descIgnore = data[4]

    def __repr__(self):
        return f"<Source \"{self.name}\">"

class Article:
    def __init__(self, title, description, link, timestamp, source: Source):
        self.title = title
        self.description = description
        self.link = link
        self.timestamp = timestamp
        self.source = source

    def __repr__(self):
        return f"<Article \"{self.title}\">"

    def __eq__(self, other):
        if type(other) is Article:
            return(self.link == other.link)

    def create_embed(self, config=None):
        embed = discord.Embed(
            title = self.title,
            description = self.description,
            color = discord.Colour(config.get("embed_colour")) if config else 0,
            timestamp = datetime.fromtimestamp(mktime(self.timestamp))
        )
        embed.set_author(name=self.source.name, icon_url=self.source.icon)
        embed.add_field(name="Read This Story", value=self.link)
        embed.set_footer(
            text = f"News-Bot does not represent nor endorse {self.source.name}.", 
            icon_url = config.get("embed_author_icon") if config else ""
        )
        return embed

async def get_sources():
    async with aiosqlite.connect("db.sqlite3") as db:
        async with db.execute("SELECT * FROM sources") as cursor:
            return [Source(i) for i in await cursor.fetchall()]

async def fetch_feeds(loop):
    global firstRun
    results = []
    sources = await get_sources()
    for i in sources:
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.get(i.url) as response:
                xml = await response.text()
                rss = feedparser.parse(xml)
                try:
                    selected = sorted([i for i in rss.entries if i.get("published_parsed")], key=lambda x: x.published_parsed, reverse=True)[0]
                except Exception as error:
                    print(f"`{i.short}` failed in selection with error `{error}`")
                else:
                    result = Article(
                        selected.title, 
                        selected.description if selected.get("description") and not i.descIgnore else "No description.", 
                        selected.link, 
                        selected.published_parsed,
                        i
                    )
                    if result not in feed:
                        feed.append(result)
                        #if firstRun: continue
                        results.append(result)
    firstRun = False
    return results

class feeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_task = self.bot.loop.create_task(self.post_all())

    async def post_all(self):
        global firstRun, feed
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            results = await fetch_feeds(self.bot.loop)
            async with aiosqlite.connect("db.sqlite3") as db:
                for i in results:
                    embed = i.create_embed(config=self.bot._config)
                    async with db.execute(f"SELECT channelId FROM subscriptions WHERE source=\"{i.source.short}\";") as cursor:
                        clients = await cursor.fetchall()
                        for c in clients:
                            try:
                                await self.bot.get_channel(int(c[0])).send(embed=embed)
                            except:
                                continue
            await sleep(self.bot._config.get("feeds_delay"))
            print(feed)
            print("repeat")

    @commands.command()
    async def feed(self, ctx):
        global feed
        await ctx.send(feed)

    @commands.command()
    async def latest(self, ctx):
        global feed
        async with aiosqlite.connect("db.sqlite3") as db:
            await ctx.send(ctx.guild.id)
            async with db.execute(f"SELECT source FROM subscriptions WHERE clientId={ctx.guild.id};") as cursor:
                sources = [i[0] for i in await cursor.fetchall()]
                for i in feed[::-1]:
                    if i.source.short in sources:
                        await ctx.send(embed=i.create_embed(config=self.bot._config))
                        break

def setup(bot):
    bot.add_cog(feeds(bot))

if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(fetch_feeds(loop))