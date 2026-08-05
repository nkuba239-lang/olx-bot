import time
from curl_cffi import requests

# Słownik cen rynkowych dla Vinted
BASE_PRICES_VINTED = {
    "astro bot ps5": 190,
    "black myth wukong ps5": 210,
    "silent hill 2 ps5": 140,
    "star wars outlaws ps5": 170,
    "helldivers 2 ps5": 110,
    "fc 25 ps5": 150,
    "fc 25 ps4": 110,
    "gta v ps5": 60,
    "gta v ps4": 50,
    "elden ring ps5": 90,
    "spider-man 2 ps5": 120,
    "god of war ragnarok ps5": 110,
    "hogwarts legacy ps5": 90,
    "wiedźmin 3 ps5": 90,
}


def pobierz_okazje_vinted(min_znizka_percent=15):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  session = requests.Session(impersonate="chrome110")

  # Pobieranie wstępnej cookies z Vinted
  try:
    session.get("https://www.vinted.pl", headers=headers, timeout=10)
  except Exception as e:
    print(f"❌ Vinted: Błąd łączenia ze stroną główną: {e}")
    return []

  okazje = []
  frazy = ["gra ps5", "gry ps5", "gra ps4"]

  for fraza in frazy:
    url = f"https://www.vinted.pl/api/v2/catalog/items?search_text={fraza}&order=newest_first&page=1&per_page=20"

    try:
      response = session.get(url, headers=headers, timeout=10)
      if response.status_code != 200:
        print(
            f"⚠️ Vinted status {response.status_code} dla szukania: {fraza}"
        )
        continue

      data = response.json()
      items = data.get("items", [])

      for item in items:
        tytul = item.get("title", "").lower()
        price_dict = item.get("price", {})

        # Odczyt ceny (zależnie od formatu zwrotki z Vinted)
        if isinstance(price_dict, dict):
          cena = float(price_dict.get("amount", 0))
        elif isinstance(price_dict, (int, float, str)):
          cena = float(price_dict)
        else:
          cena = 0.0

        item_url = item.get("url", "")
        photo_info = item.get("photo", {})
        zdjecie = photo_info.get("url", "") if photo_info else ""

        # Dopasowanie do słownika cen
        for gra, cena_bazowa in BASE_PRICES_VINTED.items():
          if gra in tytul and cena > 0:
            oczekiwana_cena = cena_bazowa * (1 - min_znizka_percent / 100)

            if cena <= oczekiwana_cena:
              znizka = int(round((1 - (cena / cena_bazowa)) * 100))
              okazje.append({
                  "tytul": item.get("title"),
                  "cena": cena,
                  "srednia_cena": cena_bazowa,
                  "znizka": znizka,
                  "link": item_url,
                  "zdjecie": zdjecie,
                  "zrodlo": "Vinted",
              })
              break
    except Exception as e:
      print(f"❌ Vinted: Błąd podczas pobierania '{fraza}': {e}")

    time.sleep(2)  # Bezpieczna pauza między zapytaniami

  return okazje