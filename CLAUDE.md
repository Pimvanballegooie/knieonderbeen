# VindJeFysio Netwerk — knieonderbeen.net (Knie Onderbeen Netwerk)

Deze repo is één "spoke" in een hub-and-spoke netwerk van gespecialiseerde fysiotherapie-subsites. De hub is vindjefysio.net. Deze site hoort daarnaast, samen met enkelvoet.net en heupbovenbeen.net, onder de mid-level hub beenklachten.net (cluster "Benen").

## Architectuur
- Statische HTML/CSS/vanilla JS op GitHub Pages, custom domein via CNAME.
- Gedeelde Supabase-backend, project islujznszevdynguhjdc, met anon key in de frontend.
- Gedeelde tabellen: therapeuten, praktijken, therapeut_subcategorieen, therapeut_praktijken, subcategorieen, categorieen.
- Deze repo volgt de opzet van Enkelvoetclaude (enkelvoet.net), niet die van de rugnek-familie: het aanmeldbestand heet `therapeut-worden.html` (niet `therapeut-aanmelden.html`), en er zijn ook `locatie-worden.html`, `mijn-praktijk.html`, `partners.html`, `beheer.html`, `contact.html`, `faq.html`. Er is een aparte `sync_locaties.py` + `.github/workflows/sync-locaties.yml` die `locaties.json` genereert, naast `sync_protocollen.py` + `.github/workflows/sync-protocollen.yml` + `genereer_structured_data.py` (injecteert JSON-LD SEO-data terug in `index.html`).
- De homepage (`index.html`) is **landelijk** opgezet (geen regiofocus) en rendert praktijken uit `locaties.json` op een kaart gecentreerd op Nederland ([52.2, 5.3]), met een live discipline-filter.
- Palet identiek aan enkelvoet.net en beenklachten.net (bewust gedeeld binnen het "Benen"-cluster): navy #1B3A5C, teal #2A9D8F, teal-light #E8F5F4.
- Logo is het Beenklachten-logo (`BKN_Logo.png`), gedeeld door alle drie de Benen-subsites.

## Belangrijke conventies
- therapeut-worden.html linkt ALTIJD relatief/lokaal binnen de eigen subsite (nooit naar vindjefysio.net). Ondersteunt meerdere praktijkcodes per therapeut (multi-locatie).
- locatie-worden.html is een uitlegpagina die doorlinkt naar het centrale vindjefysio.net/aanmelden.html?via=knieonderbeen.net.
- Mails lopen via info@vindjefysio.net; beheer.html verstuurt zelf ook mails (praktijkcode-bevestiging, therapeut-uitnodiging) via de gedeelde Supabase Edge Function `functions/v1/smart-worker` (geen lokale Resend-code).
- ⚠️ Subcategorie-koppeling voor therapeuten gebeurt NIET automatisch bij aanmelding — therapeut-worden.html vraagt geen specialisatie en zet geen subcategorie. De koppeling gebeurt volledig handmatig door een beheerder via het "Specialisaties"-tabblad in beheer.html (tabel therapeut_subcategorieen, met een `niveau`-veld, standaard 'basis').
- Deze site: subcategorie 44 (Knie en onderbeen) is het primaire domein; 46 (Artroseprogramma's), 47 (Revalidatie na operatie), 48 (Voorbereiding op operatie), 49 (Sport, bewegen en overbelasting) zijn de gedeelde been-thema's (categorie "Benen" in Supabase, subcats 43–49, zie ook beenklachten.net).
- Disciplines: Fysiotherapeut, Manueel therapeut, Sportfysiotherapeut, Oefentherapeut (zelfde lijst als beenklachten.net — bewust afwijkend van enkelvoet.net's podotherapie/pedicure-lijst, die hier niet relevant is).
- Cursusplatform: nog geen content. `MODULES = []` in mijn-profiel.html, met een "binnenkort"-lijst van placeholder-modules voor knie/onderbeen. Cursustoegang blijft, zoals bij enkelvoet.net, tier-gated (alleen praktijken met tier plus/partner).

## Sync-pipeline
- sync_locaties.py haalt actieve praktijken/therapeuten op uit Supabase, filtert (ANDERS dan enkelvoet.net) op subcategorie-koppeling in de set [44, 46, 47, 48, 49], geocodeert via Nominatim, schrijft locaties.json. Workflow git-add: locaties.json.
- sync_protocollen.py haalt protocollen op uit publiek gedeelde Google Docs (export-link, geen API-key), zet markdown om naar HTML op drie niveaus (makkelijk/gemiddeld/complex), genereert protocollen/<id>-<niveau>.html + protocollen.html + sitemap.xml. genereer_structured_data.py injecteert daarna JSON-LD terug in index.html. Workflow git-add: protocollen/ protocollen.html sitemap.xml robots.txt index.html.
- Zones (protocollen-config.json): knie, onderbeen.
- Google Docs moeten op "iedereen met de link kan bekijken" staan.

## Relatie tot beenklachten.net
- beenklachten.net toont deze site nu nog als "Binnenkort" (in index.html en aanmelden.html); dat wordt in een aparte, latere stap bijgewerkt naar "Actief" met een live link zodra deze site gereed is.
- Aangemelde therapeuten/praktijken hier verschijnen automatisch ook op beenklachten.net via de gedeelde subcats 43–49 (live Supabase-query daar, niets gegenereerd).
