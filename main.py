import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Mémoire intelligente : produit -> dernier état connu ("stock" ou "rupture")
known_status = {}

WATCHED_SITES = [
    {"name": "Tycap TCG", "url": "https://tycap-tcg.com", "selector": "body", "condition": lambda text: any(p in text.lower() for p in ["pokemon", "pokémon"]) and any(k in text.lower() for k in ["booster", "display", "etb", "coffret", "deck", "pokémon", "pokémon tcg", "pokemon tcg"]), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemael", "url": "https://pokemael.com", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Guizette Family", "url": "https://www.guizettefamily.com", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Kairyu", "url": "https://kairyu.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Poke-Geek", "url": "https://www.poke-geek.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokestation", "url": "https://pokestation.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Le Coin des Barons", "url": "https://lecoindesbarons.com", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Blazing Tail", "url": "https://www.blazingtail.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pikastore", "url": "https://www.pikastore.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemoms", "url": "https://pokemoms.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Cards Hunter", "url": "https://www.cardshunter.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Fantasy Sphere", "url": "https://www.fantasysphere.net", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemagic", "url": "https://pokemagic.fr", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "InvestCollect", "url": "https://investcollect.com", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Fnac", "url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0%211&Search=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Cultura", "url": "https://www.cultura.com/jeux-jouets/jeux-de-cartes/pokemon.html", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Micromania", "url": "https://www.micromania.fr/search.html?query=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Smyths Toys", "url": "https://www.smythstoys.com/fr/fr-fr/jouets/cartes-%C3%A0-jouer/pokemon/c/SM06010101", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Leclerc", "url": "https://www.e.leclerc/catalogue/search?query=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Auchan", "url": "https://www.auchan.fr/recherche?text=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()}
]

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    check_preorders.start()

@tasks.loop(minutes=2)
async def check_preorders():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Salon introuvable.")
        return

    for site in WATCHED_SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            image_url = None
            elements = soup.select(site["selector"])

            for el in elements:
                text = el.get_text(strip=True)
                img_tag = el.find("img")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None
                if site["condition"](text):
                    unique_key = f"{site['name']}::{text[:100]}"
                    stock_status = "stock" if site["stock_check"](text) else "rupture"

                    if unique_key not in known_status:
                        known_status[unique_key] = stock_status
                        if stock_status == "stock":
                            embed = discord.Embed(
                                title=f"🛒 Nouveau produit en STOCK chez {site['name']}",
                                description=text[:300] + "..." if len(text) > 300 else text,
                                url=site["url"],
                                color=discord.Color.green()
                            )
                            if image_url:
                                embed.set_image(url=image_url)
                            await channel.send(embed=embed)
                    elif known_status[unique_key] != stock_status:
                        known_status[unique_key] = stock_status
                        if stock_status == "stock":
                            embed = discord.Embed(
                                title=f"🔁 RESTOCK chez {site['name']} !",
                                description=text[:300] + "..." if len(text) > 300 else text,
                                url=site["url"],
                                color=discord.Color.orange()
                            )
                            await channel.send(embed=embed)

        except Exception as e:
            print(f"Erreur avec {site['name']} : {e}")

@bot.command()
async def ping(ctx):
    await ctx.send("🟢 Le bot est en ligne et fonctionne !")

@bot.command()
async def derniers(ctx):
    if not known_status:
        await ctx.send("Aucune donnée enregistrée pour l'instant.")
        return

    message = "\n".join(f"- {key.split('::')[0]} : {status}" for key, status in list(known_status.items())[-10:])
    await ctx.send(f"🗂 **10 derniers produits suivis :**\n{message}")

@bot.command()
async def sites(ctx):
    site_list = "\n".join(f"- {site['name']}" for site in WATCHED_SITES)
    await ctx.send(f"🔎 **Sites actuellement surveillés :**\n{site_list}")

bot.run(TOKEN)
