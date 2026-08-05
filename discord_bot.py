import os
import json
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

try:
    from olx import pobierz_oferty as pobierz_okazje
except ImportError:
    from olx import pobierz_okazje

from vinted import pobierz_okazje_vinted

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))
PORT = int(os.environ.get("PORT", 10000))

SLOWNIK_CEN = {
    "astro bot": 180,
    "gta v": 500,  
    "gta 5": 500,
    "god of war ragnarok": 120,
    "spiderman 2": 160,
    "elden ring": 130,
    "fifa 25": 150,
    "ea fc 25": 150,
    "the last of us part 1": 130,
    "the last of us part 2": 90,
    "cyberpunk 2077": 80,
    "red dead redemption 2": 70,
    "witcher 3": 50,
    "wiedźmin 3": 50
}

# Czysta baza na czas testu (żeby wysłało wszystko)
def wczytaj_wyslane():
    return set()

def zapisz_wyslane(baza):
    pass

wyslane_linki = wczytaj_wyslane()

# Flask Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako: {bot.user.name}", flush=True)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Bot wystartował! Rozpoczynam pierwsze skanowanie...**")
    
    # Bezpośrednie uruchomienie taska
    if not sprawdzaj_okazje.is_running():
        sprawdzaj_okazje.start()

@tasks.loop(minutes=3)
async def sprawdzaj_okazje():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Brak dostępu do kanału Discord! Sprawdź CHANNEL_ID.", flush=True)
        return

    print("🔎 Rozpoczynam skanowanie OLX i Vinted...", flush=True)
    
    # 1. OLX
    try:
        okazje_olx = await asyncio.to_thread(pobierz_okazje, SLOWNIK_CEN, 15)
        print(f"Pobrano z OLX: {len(okazje_olx)} ofert", flush=True)
    except Exception as e:
        print(f"❌ Błąd OLX: {e}", flush=True)
        okazje_olx = []

    # 2. Vinted
    try:
        okazje_vinted = await asyncio.to_thread(pobierz_okazje_vinted, SLOWNIK_CEN, 15)
        print(f"Pobrano z Vinted: {len(okazje_vinted)} ofert", flush=True)
    except Exception as e:
        print(f"❌ Błąd Vinted: {e}", flush=True)
        okazje_vinted = []

    wszystkie_okazje = okazje_olx + okazje_vinted
    znaleziono_nowe = 0

    for okazja in wszystkie_okazje:
        link = okazja.get('link')
        if link and link not in wyslane_linki:
            wyslane_linki.add(link)
            znaleziono_nowe += 1
            
            zrodlo = okazja.get('zrodlo', 'OLX')
            kolor = discord.Color.green() if zrodlo == 'Vinted' else discord.Color.blue()

            embed = discord.Embed(
                title=f"🔥 OKAZJA {zrodlo}: {okazja['tytul']}",
                url=link,
                color=kolor
            )
            embed.add_field(name="Cena", value=f"**{okazja['cena']} zł**", inline=True)
            embed.add_field(name="Cena rynkowa", value=f"{okazja['cena_rynkowa']} zł", inline=True)
            embed.add_field(name="Taniej o", value=f"**{okazja['procent']}%**", inline=True)
            
            if okazja.get('foto'):
                embed.set_thumbnail(url=okazja['foto'])

            await channel.send(embed=embed)
            await asyncio.sleep(1)

    print(f"📊 Zakończono skanowanie. Wysłano nowych okazji: {znaleziono_nowe}", flush=True)

# Start Flask & Bot
Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
