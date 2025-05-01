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

# Mémoire intelligente : produit -> dernier état connu ("stock" ou "rupture")
known_status = {}

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

@tasks.loop(minutes=2)
async def check_sites():
    channel = bot.get_channel(CHANNEL_ID)
    for site in WATCHED_SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            product_links = [a for a in soup.find_all("a", href=True) if "pokemon" in a.get_text().lower() or "pokemon" in a["href"].lower()]

            new_found = []
            for link in product_links:
                full_url = urljoin(site["url"], link["href"])
                if full_url not in known_status:
                    known_status[full_url] = True
                    new_found.append(full_url)

            if new_found:
                for product in new_found:
                    await channel.send(f"🆕 **{site['name']}** : nouveau produit Pokémon détecté !\n{product}")
            

        except Exception as e:
            await channel.send(f"⚠️ Erreur sur {site['name']} : {str(e)}")

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    check_sites.start()

bot.run(TOKEN)
