import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Liste de sites à surveiller avec leurs règles de scraping
WATCHED_SITES = [
    {
        "name": "Playin",
        "url": "https://www.play-in.com/jeux-de-cartes/pokemon/",
        "checker": lambda soup: any("precommande" in el.text.lower() for el in soup.select(".product-list .media-body"))
    },
    {
        "name": "UltraJeux",
        "url": "https://www.ultrajeux.com/",
        "checker": lambda soup: "pok" in soup.text.lower() and "precommande" in soup.text.lower()
    },
    {
        "name": "Pokegourou",
        "url": "https://pokegourou.com/collections/pokemon-precommande",
        "checker": lambda soup: len(soup.select(".product-item")) > 0
    },
    {
        "name": "Pokebox",
        "url": "https://pokebox.fr/collections/precommandes",
        "checker": lambda soup: len(soup.select(".product-grid-item")) > 0
    },
    {
        "name": "Derivstore",
        "url": "https://www.derivstore.fr/",
        "checker": lambda soup: "pokemon" in soup.text.lower() and "precommande" in soup.text.lower()
    },
    {
        "name": "ShopForgeek",
        "url": "https://shopforgeek.com/collections/pokemon",
        "checker": lambda soup: len(soup.select(".product-card")) > 0
    },
    {
        "name": "PokecenterShop",
        "url": "https://pokecentershop.fr/collections/precommandes",
        "checker": lambda soup: len(soup.select(".product-item")) > 0
    },
    {
        "name": "Ludivers",
        "url": "https://www.ludivers.com/pokemon",
        "checker": lambda soup: "precommande" in soup.text.lower()
    },
]

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    check_preorders.start()

@tasks.loop(minutes=1)
async def check_preorders():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Salon introuvable.")
        return

    for site in WATCHED_SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            if site["checker"](soup):
                await channel.send(f"📦 **Précommande détectée chez {site['name']}** !\n🔗 {site['url']}")
        except Exception as e:
            print(f"Erreur avec {site['name']} : {e}")

@bot.command()
async def ping(ctx):
    await ctx.send("🟢 Le bot est en ligne et fonctionne !")

bot.run(TOKEN)
