import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from urllib.parse import urljoin

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Date et heure du démarrage du bot
start_time = datetime.now()

# Mémoire intelligente : produit -> statut ("stock" ou "rupture")
known_status = {}
initialized = False

WATCHED_SITES = [
    {"name": "Tycap TCG", "url": "https://tycap-tcg.com/collections/all"},
    {"name": "Pokemael", "url": "https://pokemael.com/collections/all"},
    {"name": "Guizette Family", "url": "https://www.guizettefamily.com/collections/all"},
    {"name": "Kairyu", "url": "https://kairyu.fr/collections/all"},
    {"name": "Poke-Geek", "url": "https://www.poke-geek.fr/collections/all"},
    {"name": "Pokestation", "url": "https://pokestation.fr/collections/all"},
    {"name": "Le Coin des Barons", "url": "https://lecoindesbarons.com/collections/all"},
    {"name": "Blazing Tail", "url": "https://www.blazingtail.fr/collections/all"},
    {"name": "Pikastore", "url": "https://www.pikastore.fr/collections/all"},
    {"name": "Pokemoms", "url": "https://pokemoms.fr/collections/all"},
    {"name": "Cards Hunter", "url": "https://www.cardshunter.fr/collections/all"},
    {"name": "Fantasy Sphere", "url": "https://www.fantasysphere.net/collections/all"},
    {"name": "Pokemagic", "url": "https://pokemagic.fr/collections/all"},
    {"name": "InvestCollect", "url": "https://investcollect.com/collections/all"},
    {"name": "Fnac", "url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0%211&Search=pokemon+tcg"},
    {"name": "Cultura", "url": "https://www.cultura.com/jeux-jouets/jeux-de-cartes/pokemon.html"},
    {"name": "Micromania", "url": "https://www.micromania.fr/search.html?query=pokemon+tcg"},
    {"name": "Smyths Toys", "url": "https://www.smythstoys.com/fr/fr-fr/jouets/cartes-%C3%A0-jouer/pokemon/c/SM06010101"},
    {"name": "Leclerc", "url": "https://www.e.leclerc/catalogue/search?query=pokemon+tcg"},
    {"name": "Auchan", "url": "https://www.auchan.fr/recherche?text=pokemon+tcg"}
]

@tasks.loop(seconds=30)
async def check_sites():
    global initialized
    channel = bot.get_channel(CHANNEL_ID)
    for site in WATCHED_SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            product_links = [a for a in soup.find_all("a", href=True) if "pokemon" in a.get_text().lower() or "pokemon" in a["href"].lower()]

            for link in product_links:
                full_url = urljoin(site["url"], link["href"])
                text = link.get_text().lower()
                status = "stock" if not any(word in text for word in ["rupture", "épuisé", "indisponible"]) else "rupture"

                if full_url not in known_status:
                    known_status[full_url] = status
                    if initialized and status == "stock":
                        await channel.send(f"🆕 **{site['name']}** : nouveau produit Pokémon détecté !\n{full_url}")
                else:
                    last_status = known_status[full_url]
                    if last_status != status:
                        known_status[full_url] = status
                        if status == "stock":
                            await channel.send(f"🔁 **{site['name']}** : RESTOCK détecté !\n{full_url}")

        except Exception as e:
            await channel.send(f"⚠️ Erreur sur {site['name']} : {str(e)}")

    if not initialized:
        initialized = True
        print("🔄 Première initialisation terminée : mémoire remplie sans alertes.")

@bot.command()
async def reset(ctx):
    global known_status, initialized
    known_status = {}
    initialized = False
    await ctx.send("🔄 Mémoire du bot réinitialisée. Tous les produits seront re-scannés.")

@bot.command()
async def status(ctx):
    uptime = datetime.now() - start_time
    minutes, seconds = divmod(uptime.seconds, 60)
    await ctx.send(f"⏱️ Le bot tourne depuis {uptime.days}j {minutes}min {seconds}s.
📦 Produits suivis actuellement : {len(known_status)}")

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    check_sites.start()

bot.run(TOKEN)
