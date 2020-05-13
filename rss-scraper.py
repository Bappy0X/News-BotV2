import aiohttp, feedparser
from asyncio import sleep,get_event_loop
import async_timeout
from datetime import datetime

##TODO: Transfer to either MongoDB or SQLite
from json import load
with open("sources.json") as file:
    sources = load(file)
firstRun = True
feed = []

class Article:
    def __init__(self, title, description, link, timestamp, sourceName, logo):
        self.title = title
        self.link = link
        self.description = description
        self.sourceName = sourceName
        self.timestamp = timestamp
        self.logo = logo
    def __repr__(self):
        return f"<Article \"{self.title}\">"
    def __eq__(self, other):
        if type(other) is Article:
            return(self.link == other.link)

async def fetchfeeds(loop, sources=None):
    results = []
    for i in sources:
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.get(i["url"]) as response:
                xml = await response.text()
                rss = feedparser.parse(xml)
                try:
                    selected = sorted([i for i in rss.entries if i.get("published_parsed")], key=lambda x: x.published_parsed, reverse=True)[0]
                except Exception as error:
                    print(f"`{i['short']}` failed in selection with error `{error}`")
                else:
                    result = Article(
                        selected.title, 
                        selected.description if selected.get("description") and not i["descIgnore"] else "No description.", 
                        selected.link, 
                        selected.published_parsed,
                        i["name"],
                        i["icon"]
                    )
                    results.append(result)
    return results

async def fetchall(loop):
    global sources, firstRun, feed
    while True:
        results = await fetchfeeds(loop, sources)
        for i in results:
            if i not in feed:
                feed.append(i)
                if firstRun:
                    firstRun = False
                else:
                    pass
        await sleep(2)##TODO: Set to bot config
        print("repeat")

def setup(bot):
    pass

if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(fetchall(loop))