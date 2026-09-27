📄 README.md for CiefpEPGinfo v1.2
# CiefpEPGinfo

![Version](https://img.shields.io/badge/version-1.2-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-green.svg)
![Enigma2](https://img.shields.io/badge/enigma2-plugin-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**CiefpEPGinfo** – An FHD EPG Info plugin featuring TMDB/OMDb data enrichment and GROQ AI translation.

It displays the EPG list for the current channel on the left and detailed information about the movie or series on the right 
(poster, ratings, genre, director, description, cast). 
It automatically fetches data from TMDB and OMDb, with an option to translate descriptions using GROQ AI.
 ![CiefpEPGinfo Main Screen](https://i.postimg.cc/T3bRDvJp/1-0-19-3398-C9D-3-EB0000-0-0-0-20260927131601.jpg)

---

## ✨ Features

- 📺 **EPG List** – current + next 11 events
- 🎬 **TMDB Integration** – poster, rating, genre, director, description, cast
- ⭐ **IMDb Rating** via OMDb API
- 🌍 **GROQ AI Translation** – 20+ languages, with caching
- 🎭 **Cast 2×5** – cast display in two columns
- 🎥 **Filmography Browser** – explore actor filmography
- 👥 **Cast Explorer** – actor details on the same screen
- ▶️ **Trailer** – YouTube trailer via yt-dlp (Info button)
- 🖼️ **Smart Placeholders** – sports, news, music, kids, documentary, movie, series
- 🚫 **Non-TMDB Detection** – sports, news, music, kids, documentaries
- 🔍 **Smart TMDB Search** – title similarity (not just popularity)
- 🛡️ **Generic Title Skip** – skips TMDB lookup for "News", "Daily News", etc.
- 💾 **Cache** – stores posters and translations
- 🔄 **Auto-update** – checks for new versions on GitHub
- 🎨 **FHD Skin** – 1920×1080
- 🖼️ **PiconManager** – support for `/picon/` and `/picon/logos/`

---

## 📸 Screenshots

### Main Screen – Movie
![Movie](https://i.postimg.cc/2jLn3VBD/ciefpepginfo-1.jpg)

### Main Screen – Series
![Series](https://i.postimg.cc/QMnWd38V/ciefpepginfo-2.jpg)

### Actor Profile
![Actor](https://i.postimg.cc/R08NzLdn/ciefpepginfo-3.jpg)

### Filmography Browser
![Filmography](https://i.postimg.cc/GtR3c7sW/ciefpepginfo-5.jpg)

### Settings
![Settings](https://i.postimg.cc/j5HKkHkh/ciefpepginfo-6.jpg)

### Non-TMDB content (Sport)
![Sport](https://i.postimg.cc/X7hhdZsc/ciefpepginfo-7.jpg)

# 🔑 Configuration
When you open the plugin for the first time, go to Settings (blue button) and enter the API keys:

Key	Where to get it	Free? 
- TMDB API Key	https://www.themoviedb.org/settings/api	✅ Yes
- OMDb API Key	https://www.omdbapi.com/apikey.aspx	✅ Yes (1000/day)
- GROQ API Key	https://console.groq.com/keys	✅ Yes

Alternative – files
You can also manually create files in the plugin folder:

- /usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/tmdbapikey.txt
- /usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/omdbapikey.txt
- /usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/groqapikey.txt
The plugin will automatically load them upon startup. 

# 🎮 Buttons
Button	Action
- Exit (red)	Close plugin
- Filmography (green)	Filmography Browser
- Cast explore (yellow)	Cast Explorer
- Settings (blue)	Open Settings
- Info:Trailers (purple)	Play YouTube trailer
- MENU	Open Settings
- OK	Show details for selected EPG event
- UP/DOWN	Navigate EPG list
- BACK	Return to previous movie / close

# ⚙️ Settings
Option	Description
- TMDB API Key	TMDB key
- OMDb API Key	OMDb key (IMDb ratings)
- GROQ API Key	GROQ key (translation)
- GROQ Model	Translation model (GPT-OSS, Llama, Qwen, ...)
- Cache folder	Folder for storing posters
- Download Posters	YES/NO
- Show IMDB Rating	YES/NO
- Description lang	Language for TMDB description (en-US, sr-RS, ...)
- GROQ Translate	YES/NO – main switch
- Translate to	Translation language (sr, hr, en, ar, ...)
→ EPG description	Translate EPG description
→ TMDB Plot	Translate TMDB description
→ Biography	Translate actor biography
→ Titles	Translate titles (slower)
Cache size	Display cache size
CLEAR CACHE	Delete all posters from cache
Manual Update	Manually check for new version

# 🌍 Supported translation languages
🇷🇸 Serbian (sr)
🇭🇷 Croatian (hr)
🇧🇦 Bosnian (bs)
🇸🇮 Slovenian (sl)
🇲🇰 Macedonian (mk)
🇬🇧 English (en)
🇩🇪 German (de)
🇫🇷 French (fr)
🇪🇸 Spanish (es)
🇮🇹 Italian (it)
🇷🇺 Russian (ru)
🇵🇹 Portuguese (pt)
🇵🇱 Polish (pl)
🇨🇿 Czech (cs)
🇭🇺 Hungarian (hu)
🇷🇴 Romanian (ro)
🇧🇬 Bulgarian (bg)
🇬🇷 Greek (el)
🇹🇷 Turkish (tr)
🇳🇱 Dutch (nl)
🇸🇪 Swedish (sv)
🇸🇦 Arabic (ar) – transliteration

# 🎯 Non-TMDB detection
The plugin automatically recognizes content that is not on TMDB:

Category	Placeholder	Keyword examples
- Sport	sport.png	football, soccer, tennis, basketball, league, hockey, ...
- Music	music.png	music, concert, music, festival, ...
- News	news.png	news, daily news, news, nachrichten, ...
- Kids	kids.png	kids, children's, cartoons, ...
- Documentaries	docu.png	documentary, document, ...
- Movies	movie.png	if found on TMDB but no poster exists
- Series	series.png	if found on TMDB but no poster 

# 🎬 Filmography Browser
Clicking the green button opens a ChoiceBox listing the actors from the current movie. Then:
- Select actor → ChoiceBox with their 10 most famous movies + 10 series
- Select movie → displayed on the main screen (poster, ratings, description, cast)
- BACK → returns to the original movie

# 🎥 Trailer
Clicking the Info button (purple) launches the YouTube trailer via yt-dlp.

Note: YouTube has separated video and audio streams, so the trailer might play without sound. This is a current limitation of YouTube. 🛠️ Technical Details

# Python: 3.x

- Enigma2: OpenPLi, OpenATV, OpenBH, VTi, DreamOS
- Resolution: FHD 1920×1080
- Fonts: Regular, Bold, Console
-Dependencies: python3-requests, python3-six

# File Structure
bash
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
/bash

# 🔄 Update
The plugin automatically checks for a new version upon opening. If an update is available:

text
New version: v1.3
Install now?
[Yes] [No]
For manual update:

Settings → Manual Update

Or via SSH:

bash
wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh -O - | /bin/sh
🐛 Known Issues
Trailer without sound
YouTube has separated the video and audio streams. `yt-dlp -f best` returns only the video. The solution would be `yt-dlp -f bestvideo+bestaudio`, but that requires `ffmpeg` for merging, which Enigma2 usually lacks.

# Arabic translation
Enigma2 does not support RTL (right-to-left) text. Therefore, the Arabic translation uses transliteration (Latin script). Posters for new movies
If TMDB doesn't have a poster for a new movie yet, the movie.png placeholder is displayed.

# 📝 Changelog
v1.2 (current)
- ✨ Automatic update check from GitHub
- ✨ Smart TMDB search (title similarity)
- ✨ Skip generic titles
- ✨ Arabic translation (transliteration)
- ✨ Non-TMDB detection using word boundaries
- ✨ docu.png placeholder
- ✨ movie.png / series.png placeholder
- 🐛 Fixed PiconManager (.toString())
- 🐛 Fixed detect_non_tmdb (word boundary)
- 🎨 New FHD Settings skin

v1.0 (initial)
- 🎉 First version
- 📺 EPG list
- 🎬 TMDB integration

- ⭐ OMDb/IMDB
- 🌍 GROQ translation
- 🎭 Cast 2×5
- 🎥 Filmography Browser
- ▶️ Trailer

#⚙️ Settings
🙏 Acknowledgments
ciefp – plugin author
- TMDB – https://www.themoviedb.org
- OMDb – https://www.omdbapi.com
- GROQ – https://groq.com

Enigma2 community – for support

📜 License
MIT License – free to use, modify, and distribute.

🔗 Links
- GitHub: https://github.com/ciefp/CiefpEPGinfo
- Issues: https://github.com/ciefp/CiefpEPGinfo/issues
- Installer: https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh

Enjoy the plugin! 🎬🚀