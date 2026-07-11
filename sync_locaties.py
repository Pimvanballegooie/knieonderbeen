import json, urllib.request, urllib.parse, os, time

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def supabase_get(tabel, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{tabel}?{params}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def fix_url(url):
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    url = url.replace("http://", "https://")
    return url

def geocodeer(adres):
    try:
        q = urllib.parse.quote(adres + ", Nederland")
        u = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        r = urllib.request.Request(u, headers={"User-Agent": "KnieOnderbeenNetwerk/1.0"})
        with urllib.request.urlopen(r, timeout=10) as resp:
            res = json.loads(resp.read())
        if res:
            return float(res[0]["lat"]), float(res[0]["lon"])
    except Exception as e:
        print(f"Geocoding fout: {e}")
    return None, None

# Subcategorieen die relevant zijn voor het Knie Onderbeen Netwerk:
# 44 = Knie en onderbeen (eigen domein), 46-49 = gedeelde been-thema's (zie beenklachten.net)
RELEVANTE_SUBCATS = {44, 46, 47, 48, 49}

# Haal alle actieve praktijken op
alle_praktijken = supabase_get("praktijken", "actief=eq.true&select=*")
print(f"{len(alle_praktijken)} actieve praktijken gevonden (netwerkbreed)")

# Haal therapeuten op per praktijk
therapeuten_raw = supabase_get("therapeuten", "actief=eq.true&select=*,therapeut_subcategorieen(subcategorie_id,subcategorieen(naam,slug,categorieen(naam,slug)))")

# Maak lookup: praktijk_id -> lijst therapeuten
therapeuten_per_praktijk = {}
for t in therapeuten_raw:
    pid = t["praktijk_id"]
    if pid not in therapeuten_per_praktijk:
        therapeuten_per_praktijk[pid] = []
    therapeuten_per_praktijk[pid].append(t)

# Filter tot praktijken met minstens één therapeut in een relevante subcategorie
relevante_praktijk_ids = set()
for t in therapeuten_raw:
    subcat_ids = {sc["subcategorie_id"] for sc in (t.get("therapeut_subcategorieen") or [])}
    if subcat_ids & RELEVANTE_SUBCATS:
        relevante_praktijk_ids.add(t["praktijk_id"])

praktijken = [p for p in alle_praktijken if p["id"] in relevante_praktijk_ids]
print(f"{len(praktijken)} praktijken relevant voor Knie Onderbeen Netwerk (subcats {sorted(RELEVANTE_SUBCATS)})")

locaties = []
geo_cache = {}

for p in praktijken:
    naam  = p.get("naam", "").strip()
    straat = (p.get('straat') or '').strip()
    stad = (p.get('stad') or '').strip()
    postcode = (p.get('postcode') or '').strip()
    adres_delen = [d for d in [straat, postcode, stad] if d]
    adres = ', '.join(adres_delen)
    volledig_adres = adres

    if not naam or not adres:
        continue

    # Geocoderen
    if volledig_adres not in geo_cache:
        geo_cache[volledig_adres] = geocodeer(volledig_adres)
        time.sleep(1)
    lat, lng = geo_cache[volledig_adres]

    if not lat:
        print(f"Geen coordinaten: {volledig_adres}")
        continue

    # Haal disciplines op uit praktijken tabel direct
    disc_raw = p.get("disciplines") or []
    disciplines = set(d.strip() for d in disc_raw if d)

    # Therapeuten + hun disciplines
    therapeuten_lijst = []
    therapeut_disciplines = set()
    for t in therapeuten_per_praktijk.get(p["id"], []):
        therapeuten_lijst.append({
            "naam": f"{t.get('voornaam', '')} {t.get('achternaam', '')}".strip(),
            "foto": t.get("foto_url", ""),
            "bio": t.get("bio", ""),
            "disciplines": t.get("disciplines") or []
        })
        # Verzamel alle disciplines van therapeuten bij deze praktijk
        for d in (t.get("disciplines") or []):
            if d:
                therapeut_disciplines.add(d)

    tier = p.get("tier", "basis") or "basis"

    locaties.append({
        "id":           p.get("id"),
        "naam":         naam,
        "adres":        volledig_adres,
        "postcode":     postcode,
        "website":      fix_url(p.get("website", "")),
        "telefoon":     p.get("telefoon", "").strip(),
        "email":        p.get("email", "").strip(),
        "disciplines":  sorted(list(disciplines)) if disciplines else sorted(list(therapeut_disciplines)),
        "therapeut_disciplines": sorted(list(therapeut_disciplines)),
        "tier":         tier,
        "beschrijving": p.get("beschrijving", "") if tier in ["plus", "partner"] else "",
        "logo_url":     fix_url(p.get("logo_url", "")) if tier == "partner" else "",
        "therapeuten":  therapeuten_lijst,
        "lat":          lat,
        "lng":          lng
    })
    print(f"OK: {naam} ({tier}) — {len(therapeuten_lijst)} therapeuten")

# Sorteer op tier
locaties.sort(key=lambda l: {"partner": 0, "plus": 1, "basis": 2}.get(l["tier"], 3))

with open("locaties.json", "w", encoding="utf-8") as f:
    json.dump(locaties, f, ensure_ascii=False, indent=2)

print(f"Klaar: {len(locaties)} locaties opgeslagen")
