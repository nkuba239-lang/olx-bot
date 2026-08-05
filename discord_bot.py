import asyncio
import os
import threading
import discord
from discord.ext import tasks
from flask import Flask
from olx import szukaj_okazji

# --- SERWER FLASK DLA RENDERA ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot OLX działa 24/7!'


def run_flask():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


threading.Thread(target=run_flask, daemon=True).start()
# --------------------------------

TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = 1533864846527955157

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
wyslane_linki = set()


@bot.event
async def on_ready():
  print(f'✅ Zalogowano jako: {bot.user}')

  # Powiadomienie startowe na Discordzie
  channel = bot.get_channel(CHANNEL_ID)
  if channel:
    await channel.send('🚀 **Bot OLX uruchomiony! Skanowanie w toku...**')
  else:
    print(f'❌ BŁĄD: Bot nie widzi kanału {CHANNEL_ID}!')

  if not check_olx_loop.is_running():
    check_olx_loop.start()


@tasks.loop(minutes=3)
async def check_olx_loop():
  print('🔎 [1/3] Rozpoczynam sprawdzanie OLX...')
  channel = bot.get_channel(CHANNEL_ID)

  if not channel:
    print(f'❌ Brak dostępu do kanału {CHANNEL_ID}')
    return

  try:
    okazje = await asyncio.to_thread(szukaj_okazji, min_znizka_percent=15)
    print(f'📊 [2/3] Znaleziono okazji w tym cyklu: {len(okazje)}')

    nowe_okazje = 0
    for o in okazje:
      if o['link'] not in wyslane_linki:
        wyslane_linki.add(o['link'])
        nowe_okazje += 1

        embed = discord.Embed(
            title=f"🔥 OKAZJA: {o['tytul']}",
            url=o['link'],
            color=discord.Color.green(),
        )
        embed.add_field(name='Cena', value=f"**{o['cena']} zł**", inline=True)
        embed.add_field(
            name='Cena rynkowa', value=f"{o['srednia_cena']} zł", inline=True
        )
        embed.add_field(
            name='Taniej o', value=f"**{o['znizka']}%**", inline=True
        )

        if o['zdjecie']:
          embed.set_image(url=o['zdjecie'])

        await channel.send(embed=embed)
        print(f"✅ Wysłano na Discord: {o['tytul']}")
        await asyncio.sleep(1)

    print(f'✅ [3/3] Zakończono. Nowych powiadomień: {nowe_okazje}')

  except Exception as e:
    print(f'❌ Błąd podczas skanowania: {e}')


@check_olx_loop.before_loop
async def before_check():
  await bot.wait_until_ready()


if TOKEN:
  bot.run(TOKEN)
else:
  print('❌ BŁĄD: Brak DISCORD_TOKEN!')
