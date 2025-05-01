import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Mémoire intelligente : produit -> dernier état connu ("stock" ou "rupture")
known_status = {}

WATCHED_SITES = [
    {"name": "Tycap TCG", "url": "https://tycap-tcg.com/collections/all", "selector": "body", "condition": lambda text: any(p in text.lower() for p in ["pokemon", "pokémon"]) and any(k in text.lower() for k in ["booster", "display", "etb", "coffret", "deck", "pokémon", "pokémon tcg", "pokemon tcg"]), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemael", "url": "https://pokemael.com/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Guizette Family", "url": "https://www.guizettefamily.com/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Kairyu", "url": "https://kairyu.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Poke-Geek", "url": "https://www.poke-geek.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokestation", "url": "https://pokestation.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Le Coin des Barons", "url": "https://lecoindesbarons.com/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Blazing Tail", "url": "https://www.blazingtail.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pikastore", "url": "https://www.pikastore.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemoms", "url": "https://pokemoms.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Cards Hunter", "url": "https://www.cardshunter.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Fantasy Sphere", "url": "https://www.fantasysphere.net/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Pokemagic", "url": "https://pokemagic.fr/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "InvestCollect", "url": "https://investcollect.com/collections/all", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Fnac", "url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0%211&Search=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Cultura", "url": "https://www.cultura.com/jeux-jouets/jeux-de-cartes/pokemon.html", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Micromania", "url": "https://www.micromania.fr/search.html?query=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Smyths Toys", "url": "https://www.smythstoys.com/fr/fr-fr/jouets/cartes-%C3%A0-jouer/pokemon/c/SM06010101", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Leclerc", "url": "https://www.e.leclerc/catalogue/search?query=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()},
    {"name": "Auchan", "url": "https://www.auchan.fr/recherche?text=pokemon+tcg", "selector": "body", "condition": lambda text: "pokemon" in text.lower(), "stock_check": lambda text: "rupture" not in text.lower()}
]

@tasks.loop(minutes=2)
async def check_sites():
    channel = bot.get_channel(CHANNEL_ID)
    for site in WATCHED_SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.select_one(site["selector"])
            if content:
                text = content.get_text()
                product_detected = site["condition"](text)
                in_stock = site["stock_check"](text)

                last_key = f"{site['name']}_status"
                current_status = "stock" if product_detected and in_stock else "rupture"
                if known_status.get(last_key) != current_status:
                    known_status[last_key] = current_status
                    if current_status == "stock":
                        await channel.send(f"✅ **{site['name']}** : nouveau produit Pokémon en stock !\n{site['url']}")
                    else:
                        await channel.send(f"❌ **{site['name']}** : plus rien en stock.")
                else:
                    # log silencieux
                    now = datetime.now().strftime("%H:%M:%S")
                    await channel.send(f"🔍 [{now}] Vérifié : {site['name']} — aucun changement.")
        except Exception as e:
            await channel.send(f"⚠️ Erreur sur {site['name']} : {str(e)}")

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    check_sites.start()

bot.run(TOKEN)
