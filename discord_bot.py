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

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))
PORT = int(os.environ.get("PORT", 10000))

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
        await channel.send("🚀 **Bot OLX aktywny! Uruchamiam natychmiastowe skanowanie...**")
    
    # Wywołanie skanowania od razu przy wystarcie
    bot.loop.create_task(sprawdzaj_okazje())

@tasks.loop(minutes=3)
async def sprawdzaj_okazje():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Brak CHANNEL_ID", flush=True)
        return

    print("🔎 Rozpoczynam skanowanie OLX...", flush=True)
    
    try:
        okazje_olx = await asyncio.to_thread(pobierz_okazje, SLOWNIK_CEN, 15)
        print(f"Pobrano z OLX: {len(okazje_olx)} ofert", flush=True)
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
                title=f"🔥 OKAZJA OLX: {okazja['tytul']}",
                url=link,
                color=discord.Color.blue()
            )
            embed.add_field(name="Cena", value=f"**{okazja['cena']} zł**", inline=True)
            embed.add_field(name="Cena rynkowa", value=f"{okazja['cena_rynkowa']} zł", inline=True)
            embed.add_field(name="Taniej o", value=f"**{okazja['procent']}%**", inline=True)
            
            if okazja.get('foto'):
                embed.set_thumbnail(url=okazja['foto'])

            await channel.send(embed=embed)
            await asyncio.sleep(1)

    zapisz_wyslane(wyslane_linki)
    print(f"📊 Zakończono skanowanie. Wysłano nowych okazji: {znaleziono_nowe}", flush=True)

Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
