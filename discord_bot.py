import os
import json
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# Importy Twoich skryptów
from scraper import pobierz_okazje  # Skrypt OLX
from vinted import pobierz_okazje_vinted  # Skrypt Vinted

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

SLOWNIK_CEN = {
    "astro bot": 180,
    "gta v": 60,
    "gta 5": 60,
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

# Plik pamięci wysłanych linków (odporny na restarty)
PLIK_Bazy = "wyslane.json"

def wczytaj_wyslane():
    if os.path.exists(PLIK_Bazy):
        with open(PLIK_Bazy, "r") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()

def zapisz_wyslane(baza):
    with open(PLIK_Bazy, "w") as f:
        json.dump(list(baza), f)

wyslane_linki = wczytaj_wyslane()

# Flask Server (Pinging)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako: {bot.user.name}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Bot OLX + Vinted aktywny! Sprawdzanie co 3 minuty.**")
    if not sprawdzaj_okazje.is_running():
        sprawdzaj_okazje.start()

@tasks.loop(minutes=3)
async def sprawdzaj_okazje():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    print("🔎 Rozpoczynam skanowanie OLX i Vinted...")
    
    # 1. Pobieranie z OLX
    try:
        okazje_olx = await asyncio.to_thread(pobierz_okazje, SLOWNIK_CEN, 15)
    except Exception as e:
        print(f"❌ Błąd OLX: {e}")
        okazje_olx = []

    # 2. Pobieranie z Vinted
    try:
        okazje_vinted = await asyncio.to_thread(pobierz_okazje_vinted, SLOWNIK_CEN, 15)
    except Exception as e:
        print(f"❌ Błąd Vinted: {e}")
        okazje_vinted = []

    wszystkie_okazje = okazje_olx + okazje_vinted
    znaleziono_nowe = 0

    for okazja in wszystkie_okazje:
        link = okazja['link']
        if link not in wyslane_linki:
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

    zapisz_wyslane(wyslane_linki)
    print(f"📊 Zakończono skanowanie. Wysłąno nowych okazji: {znaleziono_nowe}")

# Start Flask
Thread(target=run_flask).start()

# Start Bot
bot.run(TOKEN)
