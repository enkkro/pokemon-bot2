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
    # (même contenu que dans le code actuel)
    # raccourci ici pour clarté
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
            elements = soup.select(site["selector"])

            for el in elements:
                text = el.get_text(strip=True)
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
