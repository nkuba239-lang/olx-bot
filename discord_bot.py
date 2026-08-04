import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from olx import szukaj_okazji

import os

TOKEN = os.getenv("DISCORD_TOKEN") 
CHANNEL_ID = 1533864846527955157  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SEEN_FILE = "seen_deals.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Błąd wczytywania seen_deals: {e}")
            return set()
    return set()

def save_seen(seen_set):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen_set), f)
    except Exception as e:
        print(f"Błąd zapisu seen_deals: {e}")

seen_deals = load_seen()

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako: {bot.user.name}")
    if not check_olx_loop.is_running():
        check_olx_loop.start()

@tasks.loop(minutes=3)
async def check_olx_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Nie znaleziono kanału o ID {CHANNEL_ID}!")
        return

    print("🔎 Skanuję OLX...")
    try:
        okazje = szukaj_okazji(min_znizka_percent=20)
    except Exception as e:
        print(f"❌ Błąd podczas wykonywania szukaj_okazji: {e}")
        return

    wyslane_count = 0

    for okazja in okazje:
        link = okazja.get("link")
        if not link or link in seen_deals:
            continue

        zysk = round(okazja.get("srednia_cena", 0) - okazja.get("cena", 0), 2)

        embed = discord.Embed(
            title=f"🔥 OKAZJA! -{okazja.get('znizka', 0)}% na OLX",
            url=link,
            description=f"**{okazja.get('tytul', 'Brak tytułu')}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Cena na OLX", value=f"**{okazja.get('cena', 0)} zł**", inline=True)
        embed.add_field(name="Średnia rynkowa", value=f"~~{okazja.get('srednia_cena', 0)} zł~~", inline=True)
        embed.add_field(name="Zysk", value=f"**+{zysk} zł**", inline=False)

        zdjecie_url = okazja.get("zdjecie")
        if zdjecie_url and str(zdjecie_url).startswith("http"):
            embed.set_image(url=zdjecie_url)

        embed.set_footer(text="Bot OLX • PS4/PS5")

        try:
            await channel.send(embed=embed)
            wyslane_count += 1
            seen_deals.add(link)
            save_seen(seen_deals)
            # Małe opóźnienie, aby Discord nie zablokował bota za spam (Rate Limit)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Błąd wysyłania wiadomości dla '{okazja.get('tytul')}': {e}")

    print(f"✅ Wysłano nowych okazji na Discord: {wyslane_count}")

bot.run(TOKEN)