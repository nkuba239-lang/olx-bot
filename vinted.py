import time
import re
from curl_cffi import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

def pobierz_okazje_vinted(slownik_cen, min_znizka_procent=15):
    okazje = []
    session = requests.Session(impersonate="chrome120")
    
    try:
        # Pobieranie tokenu sesji Vinted
        init_res = session.get("https://www.vinted.pl", headers=HEADERS, timeout=10)
        print(f"DEBUG Vinted Init Status: {init_res.status_code}")
    except Exception as e:
        print(f"❌ Błąd inicjalizacji Vinted: {e}")
        return okazje

    frazy = ["gra ps5", "gry ps5", "gra ps4"]
    
    for fraza in frazy:
        time.sleep(2)
        url = f"https://www.vinted.pl/api/v2/catalog/items?search_text={fraza}&order=newest_first&per_page=20"
        
        try:
            r = session.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                print(f"⚠️ Vinted zwórcił kod {r.status_code} dla frazy: {fraza}")
                continue
                
            data = r.json()
            items = data.get("items", [])
            print(f"Pobrano {len(items)} przedmiotów z Vinted dla '{fraza}'")

            for item in items:
                title = item.get("title", "")
                price_str = item.get("price", {}).get("amount", "0")
                try:
                    price = float(price_str)
                except ValueError:
                    continue

                item_url = f"https://www.vinted.pl/items/{item.get('id')}"
                photo = item.get("photos", [{}])[0].get("url", "") if item.get("photos") else ""

                for gra_klucz, cena_rynkowa in slownik_cen.items():
                    slowa = gra_klucz.lower().split()
                    title_clean = re.sub(r'[^\w\s]', '', title.lower())
                    
                    if all(s in title_clean for s in slowa):
                        max_cena = cena_rynkowa * (1 - min_znizka_procent / 100)
                        if price <= max_cena:
                            procent = round(((cena_rynkowa - price) / cena_rynkowa) * 100)
                            okazje.append({
                                'tytul': title,
                                'cena': price,
                                'cena_rynkowa': cena_rynkowa,
                                'procent': procent,
                                'link': item_url,
                                'foto': photo,
                                'zrodlo': 'Vinted'
                            })
                            
        except Exception as e:
            print(f"❌ Błąd pętli Vinted ({fraza}): {e}")

    return okazje
