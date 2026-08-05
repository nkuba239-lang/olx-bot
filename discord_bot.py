import os
import json
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

from olx import szukaj_okazji

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = 1533864846527955157
PORT = int(os.environ.get("PORT", 10000))

PLIK_BAZY = "wyslane.json"

def wczytaj_wyslane():
    if os.path.exists(PLIK_BAZY):
        try:
            with open(PLIK_BAZY, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def zapisz_wyslane(baza):
    try:
        with open(PLIK_BAZY, "w") as f:
            json.dump(list(baza), f)
    except Exception as e:
        print(f"Błąd zapisu bazy: {e}", flush=True)

wyslane_linki = wczytaj_wyslane()

app = Flask('')

@app.route('/')
def home():
    return "Bot OLX is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako: {bot.user.name}", flush=True)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Bot OLX aktywny! Skanowanie co 3 minuty.**")
    
    # Prawidłowe uruchomienie pętli, jeśli jeszcze nie działa
    if not sprawdzaj_okazje.is_running():
        sprawdzaj_okazje.start()

@tasks.loop(minutes=3)
async def sprawdzaj_okazje():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    print("🔎 Rozpoczynam skanowanie OLX...", flush=True)
    
    try:
        okazje_olx = await asyncio.to_thread(szukaj_okazji, 15)
        print(f"Pobrano z OLX: {len(okazje_olx)} okazji", flush=True)
    except Exception as e:
        print(f"❌ Błąd OLX: {e}", flush=True)
        okazje_olx = []

    znaleziono_nowe = 0

    for okazja in okazje_olx:
        link = okazja.get('link')
        if link and link not in wyslane_linki:
            wyslane_linki.add(link)
            znaleziono_nowe += 1
            
            embed = discord.Embed(
                title=f"🔥 [OLX] OKAZJA: {okazja['tytul']}",
                url=link,
                color=discord.Color.green()
            )
            embed.add_field(name="Cena", value=f"**{okazja['cena']} zł**", inline=True)
            embed.add_field(name="Cena rynkowa", value=f"**{okazja.get('srednia_cena', '---')} zł**", inline=True)
            embed.add_field(name="Taniej o", value=f"**{okazja.get('znizka', '---')}%**", inline=True)
            
            if okazja.get('zdjecie'):
                embed.set_image(url=okazja['zdjecie'])

            await channel.send(embed=embed)
            await asyncio.sleep(0.5)

    zapisz_wyslane(wyslane_linki)
    print(f"📊 Zakończono skanowanie. Wysłano nowych okazji: {znaleziono_nowe}", flush=True)

Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
