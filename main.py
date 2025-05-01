import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio
from datetime import datetime
from urllib.parse import urljoin

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

session = requests.Session()
session.headers.update(HEADERS)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

start_time = datetime.now()
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
    await scan_sites()

async def scan_sites():
    global initialized
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            log(f"❌ Salon Discord introuvable pour CHANNEL_ID = {CHANNEL_ID}")
            return

        for site in WATCHED_SITES:
            try:
                response = session.get(site["url"], timeout=(5, 10))
                if response.status_code != 200:
                    log(f"Erreur HTTP {response.status_code} sur {site['name']}")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                product_links = [a for a in soup.find_all("a", href=True) if not any(x in a["href"] for x in ["login", "account", "cart", "contact"])]

                for link in product_links:
                    full_url = urljoin(site["url"], link["href"])
                    try:
                        product_page = session.get(full_url, timeout=(5, 10))
                        if product_page.status_code == 404:
                            log(f"⛔ Lien brisé détecté (404) : {full_url}")
                            continue
                        product_soup = BeautifulSoup(product_page.text, "html.parser")
                        page_text = product_soup.get_text().lower()

                        if "pokemon" not in page_text:
                            continue

                        status = "stock" if not any(word in page_text for word in ["rupture", "épuisé", "indisponible"]) else "rupture"
                    except Exception as e:
                        log(f"Erreur produit ({full_url}) : {str(e)}")
                        continue

                    if full_url not in known_status:
                        known_status[full_url] = status
                        if initialized and status == "stock":
                            if channel:
                                await channel.send(f"🆕 **{site['name']}** : nouveau produit Pokémon détecté !\n{full_url}")
                    else:
                        last_status = known_status[full_url]
                        if last_status != status:
                            known_status[full_url] = status
                            if status == "stock":
                                if channel:
                                    await channel.send(f"🔁 **{site['name']}** : RESTOCK détecté !\n{full_url}")

                await asyncio.sleep(1)

            except Exception as e:
                log(f"Erreur sur {site['name']} : {str(e)}")

        if not initialized:
            initialized = True
            log("🔄 Première initialisation terminée : mémoire remplie sans alertes.")
    except Exception as e:
        log(f"❌ Erreur dans check_sites : {str(e)}")

@bot.command()
async def reset(ctx):
    global known_status, initialized
    known_status = {}
    initialized = False
    await ctx.send("🔄 Mémoire du bot réinitialisée. Tous les produits seront re-scannés.")

@bot.command()
async def derniers(ctx):
    if not known_status:
        await ctx.send("Aucun produit suivi pour l'instant.")
        return
    derniers = list(known_status.items())[-10:]
    message = "\n".join(f"- {url} → {status}" for url, status in derniers)
    await ctx.send(f"📝 **10 derniers produits suivis :**\n{message}")

@bot.command()
async def status(ctx):
    uptime = datetime.now() - start_time
    minutes, seconds = divmod(uptime.seconds, 60)
    await ctx.send(f"⏱️ Le bot tourne depuis {uptime.days}j {minutes}min {seconds}s.\n📦 Produits suivis actuellement : {len(known_status)}")

@bot.command()
async def rescan(ctx):
    await ctx.send("🔁 Scan manuel lancé...")
    await scan_sites()
    await ctx.send("✅ Scan terminé.")

@bot.event
async def on_ready():
    log(f"Bot connecté en tant que {bot.user}")
    try:
        check_sites.start()
    except Exception as e:
        log(f"❌ Erreur lors du démarrage de la boucle check_sites : {str(e)}")

bot.run(TOKEN)
