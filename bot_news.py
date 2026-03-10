import load_env
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import re
import os

# === KONFIGURACIJA ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID", 0))
WP_API_URL = "https://mojhub.ba/?rest_route=/wp/v2/posts"

# === DISCORD BOT ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Čuvamo već objavljene postove
posted_ids = set()
first_run = True  # indikator da je prvi put pokrenut bot

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} je aktivan.")
    check_news.start()

@tasks.loop(minutes=1)
async def check_news():
    """Provjerava WP API svakih 60 sekundi i objavljuje novosti."""
    global posted_ids, first_run
    async with aiohttp.ClientSession() as session:
        async with session.get(WP_API_URL) as resp:
            if resp.status != 200:
                print(f"⚠️ Greška pri dohvatu API-ja: {resp.status}")
                return
            data = await resp.json()

            channel = bot.get_channel(NEWS_CHANNEL_ID)
            if not channel:
                print("⚠️ Nije pronađen kanal za novosti.")
                return

            # Ako je prvi run, objavljujemo SVE postojeće novosti
            if first_run:
                posts_to_publish = list(reversed(data))  # objavi od najstarije ka najnovijoj
                first_run = False
            else:
                # Objavi samo one koje nisu već objavljene
                posts_to_publish = [p for p in reversed(data) if p["id"] not in posted_ids]

            for post in posts_to_publish:
                post_id = post.get("id")
                title = post.get("title", {}).get("rendered", "Bez naslova")
                excerpt = post.get("excerpt", {}).get("rendered", "Nema opisa")
                link = post.get("link", "#")

                # Očisti excerpt od HTML tagova
                excerpt_clean = re.sub(r"<[^>]*>", "", excerpt)

                embed = discord.Embed(
                    title=f"📢 {title}",
                    description=(excerpt_clean[:200] + "...") if excerpt_clean else "Pročitaj više na linku ispod 👇",
                    color=0x3498db,
                    url=link
                )

                # Ako ima sliku (featured_media), dohvati je
                featured_media = post.get("featured_media")
                if featured_media:
                    async with session.get(f"https://mojhub.ba/?rest_route=/wp/v2/media/{featured_media}") as media_resp:
                        if media_resp.status == 200:
                            media_data = await media_resp.json()
                            image_url = media_data.get("source_url")
                            if image_url:
                                embed.set_image(url=image_url)

                # Dodaj dugme "Saznaj više"
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Saznaj više", url=link))

                await channel.send(embed=embed, view=view)
                posted_ids.add(post_id)  # zapamti da je objavljen

# === POKRETANJE BOTA ===
bot.run(DISCORD_TOKEN)

