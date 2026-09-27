📄 README.md za CiefpEPGinfo v1.2
Evo kompletnog README-a spreman za kopiranje na GitHub:

markdown
# CiefpEPGinfo

![Version](https://img.shields.io/badge/version-1.2-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-green.svg)
![Enigma2](https://img.shields.io/badge/enigma2-plugin-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**CiefpEPGinfo** – FHD EPG Info plugin sa TMDB/OMDb enrichment-om i GROQ AI prevodom.

Prikazuje EPG listu za trenutni kanal na levoj strani, a detaljne informacije o filmu/seriji na desnoj strani (poster, ocene, žanr, režiser, opis, glumci). Automatski povlači podatke sa TMDB-a i OMDb-a, sa opcijom prevođenja opisa preko GROQ AI.

![CiefpEPGinfo Main Screen](screenshots/main.png)

---

## ✨ Funkcionalnosti

- 📺 **EPG lista** – trenutni + narednih 11 događaja
- 🎬 **TMDB integracija** – poster, ocena, žanr, režiser, opis, glumci
- ⭐ **IMDB ocena** preko OMDb API-ja
- 🌍 **GROQ AI prevod** – 20+ jezika, sa cache-om
- 🎭 **Cast 2×5** – prikaz glumaca u dve kolone
- 🎥 **Filmography Browser** – istraživanje filmografije glumaca
- 👥 **Cast Explorer** – detalji o glumcu u istom ekranu
- ▶️ **Trailer** – YouTube trailer preko yt-dlp (Info dugme)
- 🖼️ **Pametni placeholderi** – sport, news, music, kids, docu, movie, series
- 🚫 **Non-TMDB detekcija** – sport, vesti, muzika, dečiji, dokumentarci
- 🔍 **Pametna TMDB pretraga** – title similarity (ne samo popularity)
- 🛡️ **Generic titles skip** – ne ide na TMDB za "Vesti", "Dnevnik"...
- 💾 **Cache** – čuva postere i prevode
- 🔄 **Auto update** – provera nove verzije sa GitHub-a
- 🎨 **FHD skin** – 1920×1080
- 🖼️ **PiconManager** – podrška za `/picon/` i `/picon/logos/`

---

## 📸 Screenshots

### Glavni ekran – Film
![Film](screenshots/film.png)

### Glavni ekran – Serija
![Serija](screenshots/series.png)

### Profil glumca
![Actor](screenshots/actor.png)

### Filmography Browser
![Filmography](screenshots/filmography.png)

### Settings
![Settings](screenshots/settings.png)

### Non-TMDB sadržaj (Sport / News)
![Sport](screenshots/sport.png)

---

## 🔧 Instalacija

### Automatska instalacija (preporučeno)

Pokreni u SSH:

```bash
wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh -O - | /bin/sh
Installer će:

Proveriti Python verziju (2/3)

Instalirati potrebne pakete (python3-requests, python3-six)

Preuzeti plugin sa GitHub-a

Restartovati Enigmu

Manualna instalacija
Preuzmi main.tar.gz sa GitHub-a:

bash
wget https://github.com/ciefp/CiefpEPGinfo/archive/refs/heads/main.tar.gz
Raspakuj:

bash
tar -xzf main.tar.gz
Kopiraj u Enigma2:

bash
cp -r CiefpEPGinfo-main/usr /
Restartuj Enigmu:

bash
killall -9 enigma2
🔑 Konfiguracija
Kada prvi put otvoriš plugin, idi u Settings (plavo dugme) i unesi API ključeve:

Ključ	Gde nabaviti	Besplatno?
TMDB API Key	https://www.themoviedb.org/settings/api	✅ Da
OMDb API Key	https://www.omdbapi.com/apikey.aspx	✅ Da (1000/dan)
GROQ API Key	https://console.groq.com/keys	✅ Da
Alternativa – fajlovi
Možeš i ručno da kreiraš fajlove u folderu plugina:

/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/tmdbapikey.txt

/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/omdbapikey.txt

/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/groqapikey.txt

Plugin će ih automatski učitati pri startu.

🎮 Tasteri
Taster	Akcija
Exit (crveno)	Zatvori plugin
Filmography (zeleno)	Filmography Browser
Cast explore (žuto)	Cast Explorer
Settings (plavo)	Otvori Settings
Info:Trailers (ljubičasto)	Pusti YouTube trailer
MENU	Otvori Settings
OK	Prikaži detalje za odabrani EPG događaj
UP/DOWN	Navigacija kroz EPG listu
BACK	Vrati se na prethodni film / zatvori
⚙️ Settings
Opcija	Opis
TMDB API Key	Ključ za TMDB
OMDb API Key	Ključ za OMDb (IMDB ocene)
GROQ API Key	Ključ za GROQ (prevod)
GROQ Model	Model za prevod (GPT-OSS, Llama, Qwen, ...)
Cache folder	Folder za čuvanje postera
Download Posters	YES/NO
Show IMDB Rating	YES/NO
Description lang	Jezik za TMDB opis (en-US, sr-RS, ...)
GROQ Translate	YES/NO – glavni prekidač
Translate to	Jezik prevoda (sr, hr, en, ar, ...)
→ EPG description	Prevod EPG opisa
→ TMDB Plot	Prevod TMDB opisa
→ Biography	Prevod biografije glumca
→ Titles	Prevod naslova (sporije)
Cache size	Prikaz veličine cache-a
CLEAR CACHE	Briše sve postere iz cache-a
Manual Update	Ručna provera nove verzije
🌍 Podržani jezici prevoda
🇷🇸 Srpski (sr)

🇭🇷 Hrvatski (hr)

🇧🇦 Bosanski (bs)

🇸🇮 Slovenački (sl)

🇲🇰 Makedonski (mk)

🇬🇧 Engleski (en)

🇩🇪 Nemački (de)

🇫🇷 Francuski (fr)

🇪🇸 Španski (es)

🇮🇹 Italijanski (it)

🇷🇺 Ruski (ru)

🇵🇹 Portugalski (pt)

🇵🇱 Poljski (pl)

🇨🇿 Češki (cs)

🇭🇺 Mađarski (hu)

🇷🇴 Rumunski (ro)

🇧🇬 Bugarski (bg)

🇬🇷 Grčki (el)

🇹🇷 Turski (tr)

🇳🇱 Holandski (nl)

🇸🇪 Švedski (sv)

🇸🇦 Arapski (ar) – transliteracija

🎯 Non-TMDB detekcija
Plugin automatski prepoznaje sadržaj koji nije na TMDB-u:

Kategorija	Placeholder	Primeri keyword-a
Sport	sport.png	football, fudbal, tenis, košarka, liga, hokej, ...
Muzika	music.png	music, koncert, muzika, festival, ...
Vesti	news.png	vesti, dnevnik, news, nachrichten, ...
Dečiji	kids.png	kids, dečiji, crtani, ...
Dokumentarci	docu.png	documentary, dokument, ...
Filmovi	movie.png	ako TMDB nađe ali nema poster
Serije	series.png	ako TMDB nađe ali nema poster
Za detekciju koristi \b word boundary – tako da "ski" ne pogađa "televizijskih".

🔍 Pametna TMDB pretraga
Umesto da bira rezultat po popularnosti, plugin koristi kombinaciju:

Sličnost naslova (70%) – najvažnije

Godina (30% bonus ako se poklapa)

Popularity (max 20%)

Vote count (max 10%)

Ako je najbolji rezultat sličnost < 0.5 – odbija se i plugin prikazuje EPG samo.

Generic titles
Plugin preskače TMDB za generičke naslove (Vesti, Dnevnik, Program, ...) i odmah prikazuje placeholder.

🎬 Filmography Browser
Klikom na zeleno dugme otvara se ChoiceBox sa glumcima iz trenutnog filma. Zatim:

Izbor glumca → ChoiceBox sa 10 najpoznatijih filmova + 10 serija

Izbor filma → prikazuje se u glavnom ekranu (poster, ocene, opis, cast)

BACK → vraća se na originalni film

🎥 Trailer
Klikom na Info dugme (ljubičasto) pokreće se YouTube trailer preko yt-dlp.

Napomena: YouTube je odvojio video i audio stream, tako da trailer može da radi bez zvuka. To je trenutno ograničenje YouTube-a.

🛠️ Tehnički detalji
Python: 3.x

Enigma2: OpenPLi, OpenATV, OpenBH, VTi, DreamOS

Rezolucija: FHD 1920×1080

Fontovi: Regular, Bold, Console

Zavisnosti: python3-requests, python3-six

Struktura fajlova
text
/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/
├── __init__.py
├── plugin.py
├── components/
│   ├── __init__.py
│   ├── picon_manager.py
│   └── translator.py
├── icon.png
├── placeholder.png
├── sport.png
├── music.png
├── news.png
├── kids.png
├── docu.png
├── movie.png
├── series.png
├── settings.png
├── tmdbapikey.txt
├── omdbapikey.txt
└── groqapikey.txt
🔄 Update
Plugin automatski proverava novu verziju pri otvaranju. Ako je dostupan update:

text
New version: v1.3
Install now?
[Yes] [No]
Za manual update:

Settings → Manual Update

Ili preko SSH:

bash
wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh -O - | /bin/sh
🐛 Poznati problemi
Trailer bez zvuka
YouTube je razdvojio video i audio stream. yt-dlp -f best vraća samo video. Rešenje bi bilo yt-dlp -f bestvideo+bestaudio, ali to zahteva ffmpeg za merge, što Enigma2 obično nema.

Arapski prevod
Enigma2 ne podržava RTL (right-to-left) tekst. Zato arapski prevod koristi transliteraciju (latinica).

Poster nekih novih filmova
Ako TMDB još nema poster za novi film, prikazuje se movie.png placeholder.

📝 Changelog
v1.2 (aktuelna)
✨ Auto update check sa GitHub-a

✨ Pametna TMDB pretraga (title similarity)

✨ Generic titles skip

✨ Arapski prevod (transliteracija)

✨ Non-TMDB detekcija sa word boundary

✨ docu.png placeholder

✨ movie.png / series.png placeholder

🐛 Popravljen PiconManager (.toString())

🐛 Popravljen detect_non_tmdb (word boundary)

🎨 Novi FHD Settings skin

v1.0 (inicijalna)
🎉 Prva verzija

📺 EPG lista

🎬 TMDB integracija

⭐ OMDb/IMDB

🌍 GROQ prevod

🎭 Cast 2×5

🎥 Filmography Browser

▶️ Trailer

⚙️ Settings

🙏 Zahvalnice
ciefp – autor plugina

TMDB – https://www.themoviedb.org

OMDb – https://www.omdbapi.com

GROQ – https://groq.com

Enigma2 community – za podršku

📜 Licenca
MIT License – slobodno koristi, menja i distribuira.

🔗 Linkovi
GitHub: https://github.com/ciefp/CiefpEPGinfo

Issues: https://github.com/ciefp/CiefpEPGinfo/issues

Installer: https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh

Uživaj u plugin-u! 🎬🚀
