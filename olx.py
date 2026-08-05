from difflib import SequenceMatcher
import re
import time
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

WYSZUKIWANIA = [
    "elden ring",
    "gta v ps5",
    "spider man 2 ps5",
    "fifa 25 ps5",
    "fc 25",
    "cyberpunk ps5",
    "god of war ragnarok",
    "hogwarts legacy",
    "call of duty ps5",
    "the last of us ps5",
    "ghost of tsushima",
    "gra ps5",
    "gra ps4",
]

WYKLUCZONE = [
    "konsola",
    "pad",
    "dualshock",
    "dualsense",
    "vr",
    "plakat",
    "etui",
    "uchwyt",
    "stojak",
    "podstawka",
    "konto",
    "konto psn",
    "uszkodzona",
]

BASE_PRICES = {
    "wiedźmin 3 ps4": 50,
    "wiedzmin 3 ps4": 50,
    "wiedźmin 3 ps5": 90,
    "wiedzmin 3 ps5": 90,
    "gta v ps4": 50,
    "gta 5 ps4": 50,
    "gta v ps5": 60,
    "gta 5 ps5": 60,
    "cyberpunk ps4": 50,
    "cyberpunk ps5": 80,
    "god of war ps4": 25,
    "god of war ragnarok ps4": 80,
    "god of war ragnarok ps5": 110,
    "last of us ps4": 40,
    "last of us part 1 ps5": 140,
    "last of us part 2 ps4": 70,
    "fc 24 ps4": 40,
    "fc 24 ps5": 60,
    "fc 25 ps4": 110,
    "fc 25 ps5": 150,
    "spider-man ps4": 40,
    "spiderman ps4": 40,
    "spider-man miles morales ps4": 45,
    "spider-man miles morales ps5": 60,
    "spider-man 2 ps5": 120,
    "spiderman 2 ps5": 120,
    "red dead redemption 2 ps4": 50,
    "rdr 2 ps4": 50,
    "red dead redemption ps4": 70,
    "elden ring ps4": 80,
    "elden ring ps5": 90,
    "demon's souls ps5": 80,
    "demons souls ps5": 80,
    "bloodborne ps4": 25,
    "dark souls 3 ps4": 40,
    "sekiro ps4": 70,
    "hogwarts legacy ps4": 70,
    "hogwarts legacy ps5": 90,
    "ghost of tsushima ps4": 50,
    "ghost of tsushima ps5": 90,
    "ghost of tsushima director ps5": 80,
    "horizon zero dawn ps4": 20,
    "horizon forbidden west ps4": 50,
    "horizon forbidden west ps5": 70,
    "resident evil 4 ps4": 75,
    "resident evil 4 ps5": 85,
    "resident evil village ps4": 40,
    "resident evil village ps5": 50,
    "assassin's creed valhalla ps4": 35,
    "assassins creed valhalla ps4": 35,
    "assassin's creed valhalla ps5": 45,
    "assassins creed mirage ps4": 55,
    "assassins creed mirage ps5": 65,
    "call of duty modern warfare ps4": 30,
    "call of duty mw2 ps5": 90,
    "call of duty mw3 ps5": 95,
    "cod mw3 ps5": 95,
    "uncharted 4 ps4": 20,
    "uncharted kolekcja ps4": 30,
    "uncharted linia dziedzictwa ps5": 55,
    "gran turismo sport ps4": 20,
    "gt sport ps4": 20,
    "gran turismo 7 ps4": 75,
    "gran turismo 7 ps5": 100,
    "tekken 7 ps4": 25,
    "tekken 8 ps5": 120,
    "mortal kombat 11 ps4": 25,
    "mortal kombat 1 ps5": 100,
    "fifa 23 ps4": 15,
    "fifa 23 ps5": 25,
    "alan wake 2 ps5": 120,
    "silent hill 2 ps5": 130,
    "dying light 2 ps4": 40,
    "dying light 2 ps5": 60,
    "far cry 6 ps4": 30,
    "far cry 6 ps5": 40,
    "stray ps5": 55,
    "stray ps4": 50,
    "ratchet clank rift apart ps5": 80,
    "returnal ps5": 65,
    "it takes two ps4": 55,
    "it takes two ps5": 65,
    "diablo 4 ps4": 65,
    "diablo 4 ps5": 75,
    "need for speed unbound ps5": 65,
    "nfs unbound ps5": 65,
    "death stranding ps4": 25,
    "death stranding ps5": 80,
}


def czysc_cene(cena):
  try:
    cena = (
        str(cena)
        .replace("zł", "")
        .replace(",", ".")
        .replace(" ", "")
        .strip()
    )
    return float(cena)
  except:
    return None


def pobierz_strone(szukaj):
  url = f"https://www.olx.pl/d/oferty/q-{szukaj.replace(' ', '-')}/?search%5Border%5D=created_at%3Adesc"
  try:
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.text
  except:
    return ""


def czy_gra(tytul):
  t = tytul.lower()
  for x in WYKLUCZONE:
    if x in t:
      return False
  has_platform = any(k in t for k in ["ps4", "ps5", "playstation", "gra"])
  has_known_game = any(gra in t for gra in BASE_PRICES.keys())
  return has_platform or has_known_game


def pobierz_zdjecie_z_linku(link_oferty):
  try:
    r = requests.get(link_oferty, headers=HEADERS, timeout=5)
    if r.status_code == 200:
      soup = BeautifulSoup(r.text, "html.parser")
      img = soup.find(
          "img", class_=lambda c: c and "swiper" in c
      ) or soup.find("img", {"alt": True})
      if img:
        src = img.get("src") or img.get("data-src")
        if src and "http" in src and not src.endswith(".svg"):
          return src

      og_image = soup.find("meta", property="og:image")
      if og_image and og_image.get("content"):
        return og_image["content"]
  except:
    pass
  return None


def wyciagnij_oferty(html):
  soup = BeautifulSoup(html, "html.parser")
  oferty = []

  for a in soup.find_all("a", href=True):
    tytul = a.get_text(" ", strip=True)

    if len(tytul) < 5 or not czy_gra(tytul):
      continue

    link = a["href"]
    if not link.startswith("http"):
      link = "https://www.olx.pl" + link

    rodzic = a.parent.get_text(" ", strip=True)
    ceny = re.findall(r"(\d+[\s.,]?\d*)\s*zł", rodzic)

    if not ceny:
      continue

    cena = czysc_cene(ceny[0])
    if cena is None or cena < 10 or cena > 400:
      continue

    oferty.append({
        "tytul": tytul,
        "cena": cena,
        "link": link,
        "zdjecie": None,
    })

  return oferty


def pobierz_oferty():
  wszystkie = []
  for s in WYSZUKIWANIA:
    print("Szukam:", s)
    html = pobierz_strone(s)
    dane = wyciagnij_oferty(html)
    wszystkie.extend(dane)
    time.sleep(1)

  wynik = []
  linki = set()
  for x in wszystkie:
    if x["link"] not in linki:
      wynik.append(x)
      linki.add(x["link"])

  print("📦 Pobrano unikalnych ofert:", len(wynik))
  return wynik


def podobienstwo(a, b):
  a = re.sub(r"[^a-z0-9 ]", "", a.lower())
  b = re.sub(r"[^a-z0-9 ]", "", b.lower())
  return SequenceMatcher(None, a, b).ratio()


def pobierz_srednia_cene(tytul, oferty):
  tytul_lower = tytul.lower()
  sorted_keys = sorted(BASE_PRICES.keys(), key=len, reverse=True)

  for gra_klucz in sorted_keys:
    if gra_klucz in tytul_lower:
      return BASE_PRICES[gra_klucz]

  ceny = []
  for oferta in oferty:
    drugi = oferta["tytul"]
    if not czy_gra(drugi):
      continue

    if podobienstwo(tytul, drugi) >= 0.65:
      if drugi.lower() != tytul_lower:
        ceny.append(oferta["cena"])

  if len(ceny) < 3:
    return None

  ceny.sort()
  srodek = len(ceny) // 2
  mediana = (
      (ceny[srodek - 1] + ceny[srodek]) / 2
      if len(ceny) % 2 == 0
      else ceny[srodek]
  )
  return mediana


def szukaj_okazji(min_znizka_percent=15):
  oferty = pobierz_oferty()
  okazje = []

  for oferta in oferty:
    srednia = pobierz_srednia_cene(oferta["tytul"], oferty)
    if srednia and oferta["cena"] < srednia:
      znizka = int(((srednia - oferta["cena"]) / srednia) * 100)
      if znizka >= min_znizka_percent:
        oferta["srednia_cena"] = round(srednia, 2)
        oferta["znizka"] = znizka
        oferta["zdjecie"] = pobierz_zdjecie_z_linku(oferta["link"])
        okazje.append(oferta)

  print(f"🔥 Znalazłem okazji: {len(okazje)}")
  return okazje
