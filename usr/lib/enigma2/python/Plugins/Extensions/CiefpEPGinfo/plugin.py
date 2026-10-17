# -*- coding: utf-8 -*-
#
# CiefpEPGinfo - FHD EPG Info plugin with TMDB/OMDb enrichment
#
from __future__ import print_function
import os
import re
import json
import ssl
import time
import threading
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime
from difflib import SequenceMatcher
# Enigma2 imports
from Components.config import config, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo, configfile
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ScrollLabel import ScrollLabel
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from enigma import (eTimer, eEPGCache, eServiceCenter, iServiceInformation,
                    eConsoleAppContainer, eServiceReference)
from Tools.LoadPixmap import LoadPixmap
# Translator (u folderu components)
try:
    from .components.translator import Translator
except ImportError:
    try:
        from components.translator import Translator
    except ImportError:
        import sys
        sys.path.insert(0, os.path.join(PLUGIN_DIR, "components"))
        from translator import Translator
try:
    from .components.picon_manager import PiconManager
except ImportError:
    try:
        from components.picon_manager import PiconManager
    except ImportError:
        # Fallback ako se importuje kao paket
        import sys
        sys.path.insert(0, os.path.join(PLUGIN_DIR, "components"))
        from picon_manager import PiconManager
# ---------- CONFIG ----------
config.plugins.ciefpepginfo = ConfigSubsection()
config.plugins.ciefpepginfo.tmdb_api_key = ConfigText(default="", fixed_size=False)
config.plugins.ciefpepginfo.omdb_api_key = ConfigText(default="", fixed_size=False)
config.plugins.ciefpepginfo.groq_api_key = ConfigText(default="", fixed_size=False)
config.plugins.ciefpepginfo.groq_model = ConfigSelection(default="openai/gpt-oss-120b", choices=[
    ("openai/gpt-oss-120b", "GPT-OSS 120B (preporučeno)"),
    ("openai/gpt-oss-20b", "GPT-OSS 20B (brži)"),
    ("llama-3.3-70b-versatile", "Llama 3.3 70B"),
    ("llama-3.1-8b-instant", "Llama 3.1 8B (staro)"),
    ("meta-llama/llama-4-scout-17b-16e-instruct", "Llama 4 Scout 17B"),
    ("meta-llama/llama-4-maverick-17b-128e-instruct", "Llama 4 Maverick 17B"),
    ("qwen/qwen3-32b", "Qwen3 32B"),
    ("moonshotai/kimi-k2-instruct", "Kimi K2"),
    ("deepseek-r1-distill-llama-70b", "DeepSeek R1 70B"),
])
config.plugins.ciefpepginfo.cache_folder = ConfigSelection(default="/tmp/CiefpEPGinfo/", choices=[
    ("/tmp/CiefpEPGinfo/", "/tmp/CiefpEPGinfo/"),
    ("/media/hdd/CiefpEPGinfo/", "/media/hdd/CiefpEPGinfo/"),
    ("/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo/", "Plugin folder")
])
config.plugins.ciefpepginfo.cache_enabled = ConfigYesNo(default=True)
config.plugins.ciefpepginfo.language = ConfigSelection(default="en-US", choices=[
    ("en-US", "English"),
    ("sr-RS", "Srpski"),
    ("hr-HR", "Hrvatski"),
    ("bs-BA", "Bosanski"),
    ("sl-SI", "Slovenščina"),
    ("mk-MK", "Македонски"),
    ("cs-CZ", "Čeština"),
    ("sk-SK", "Slovenský"),
    ("hu-HU", "Magyar"),
    ("ro-RO", "Română"),
    ("bg-BG", "Български"),
    ("el-GR", "Ελληνικά"),
    ("de-DE", "Deutsch"),
    ("fr-FR", "Français"),
    ("es-ES", "Español"),
    ("it-IT", "Italiano"),
    ("pt-PT", "Português PT"),
    ("pt-BR", "Português BR"),
    ("nl-NL", "Nederlands"),
    ("sv-SE", "Svenska"),
    ("no-NO", "Norsk"),
    ("da-DK", "Dansk"),
    ("fi-FI", "Suomi"),
    ("ru-RU", "Русский"),
    ("uk-UA", "Українська"),
    ("pl-PL", "Polski"),
    ("tr-TR", "Türkçe"),
    ("ar-AE", "العربية"),
    ("he-IL", "עברית"),
    ("ja-JP", "日本語"),
    ("ko-KR", "한국어"),
    ("zh-CN", "中文 (简)"),
    ("zh-TW", "中文 (繁)"),
    ("th-TH", "ไทย"),
    ("vi-VN", "Tiếng Việt"),
])

config.plugins.ciefpepginfo.show_imdb_rating = ConfigYesNo(default=True)
config.plugins.ciefpepginfo.translate_epg = ConfigYesNo(default=False)
config.plugins.ciefpepginfo.translate_to = ConfigSelection(default="sr", choices=[
    ("sr", "Srpski"), ("hr", "Hrvatski"), ("bs", "Bosanski"),
    ("sl", "Slovenščina"), ("mk", "Македонски"), ("en", "English"),
    ("de", "Deutsch"), ("fr", "Français"), ("es", "Español"),
    ("it", "Italiano"), ("ru", "Русский"), ("pt", "Português"),
    ("pl", "Polski"), ("cs", "Čeština"), ("hu", "Magyar"),
    ("ro", "Română"), ("bg", "Български"), ("el", "Ελληνικά"),
    ("tr", "Türkçe"), ("nl", "Nederlands"), ("sv", "Svenska"),
    ("ar", "العربية"),
])
config.plugins.ciefpepginfo.translate_epg_description = ConfigYesNo(default=True)
config.plugins.ciefpepginfo.translate_tmdb_overview = ConfigYesNo(default=False)
config.plugins.ciefpepginfo.translate_biography = ConfigYesNo(default=False)
config.plugins.ciefpepginfo.translate_titles = ConfigYesNo(default=False)

PLUGIN_NAME = "CiefpEPGinfo"
PLUGIN_DESC = "FHD EPG Info with TMDB/OMDb enrichment"
PLUGIN_VERSION = "1.5"
PLUGIN_DIR = os.path.dirname(__file__) if '__file__' in globals() else \
    "/usr/lib/enigma2/python/Plugins/Extensions/CiefpEPGinfo"

TMDB_API_KEY_FILE = os.path.join(PLUGIN_DIR, "tmdbapikey.txt")
OMDB_API_KEY_FILE = os.path.join(PLUGIN_DIR, "omdbapikey.txt")
GROQ_API_KEY_FILE = os.path.join(PLUGIN_DIR, "groqapikey.txt")

PLACEHOLDER = os.path.join(PLUGIN_DIR, "placeholder.png")
PLACEHOLDER_SPORT = os.path.join(PLUGIN_DIR, "sport.png")
PLACEHOLDER_MUSIC = os.path.join(PLUGIN_DIR, "music.png")
PLACEHOLDER_MOVIE = os.path.join(PLUGIN_DIR, "movie.png")
PLACEHOLDER_SERIES = os.path.join(PLUGIN_DIR, "series.png")
PLACEHOLDER_NEWS = os.path.join(PLUGIN_DIR, "news.png")
PLACEHOLDER_KIDS = os.path.join(PLUGIN_DIR, "kids.png")
PLACEHOLDER_DOCU = os.path.join(PLUGIN_DIR, "docu.png")
PLUGIN_ICON = os.path.join(PLUGIN_DIR, "icon.png")
BACKGROUND_SETTINGS = os.path.join(PLUGIN_DIR, "settings.png")

VERSION_URL = "https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/version.txt"
UPDATE_COMMAND = "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpEPGinfo/main/installer.sh -O - | /bin/sh"

# ← NOVO: putanje do bouquet fajlova
USERBOUQUET_DIR = "/etc/enigma2"
LAMEDB_DIR = "/etc/enigma2"


# ---------- API KEY LOAD/SAVE ----------
def _load_key_from_file(path, cfg_attr):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                key = f.read().strip()
            if key:
                cfg = getattr(config.plugins.ciefpepginfo, cfg_attr)
                cfg.value = key
                cfg.save()
        except Exception:
            pass


def _save_key_to_file(path, value):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write((value or "").strip())
    except Exception:
        pass


def load_all_api_keys():
    _load_key_from_file(TMDB_API_KEY_FILE, "tmdb_api_key")
    _load_key_from_file(OMDB_API_KEY_FILE, "omdb_api_key")
    _load_key_from_file(GROQ_API_KEY_FILE, "groq_api_key")


# ---------- CACHE ----------
def get_cache_info():
    """Vraća (broj_fajlova, ukupno_MB) za cache folder"""
    try:
        folder = ensure_cache_folder()
        if not os.path.exists(folder):
            return 0, 0.0
        count = 0
        total = 0
        for filename in os.listdir(folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    count += 1
                    total += os.path.getsize(filepath)
        return count, total / (1024.0 * 1024.0)
    except Exception as e:
        print("[CiefpEPGinfo] get_cache_info error:", e)
        return 0, 0.0


def clear_cache():
    """Briše sve slike iz cache foldera. Vraća (broj_obrisanih, MB)"""
    try:
        folder = ensure_cache_folder()
        if not os.path.exists(folder):
            return 0, 0.0
        deleted = 0
        freed = 0
        for filename in os.listdir(folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(folder, filename)
                try:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted += 1
                    freed += size
                except Exception as e:
                    print(f"[CiefpEPGinfo] ne mogu obrisati {filepath}: {e}")
        return deleted, freed / (1024.0 * 1024.0)
    except Exception as e:
        print("[CiefpEPGinfo] clear_cache error:", e)
        return 0, 0.0

def ensure_cache_folder():
    folder = config.plugins.ciefpepginfo.cache_folder.value
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except Exception:
            pass
    return folder


def load_pixmap_safe(path):
    if path and os.path.exists(path):
        try:
            return LoadPixmap(path)
        except Exception:
            return None
    return None


# ---------- EPG ----------
def get_current_service():
    """Vraća trenutni servis – kompatibilno sa OpenPLi/OpenATV/OpenBH/VTi"""
    try:
        from Screens.InfoBar import InfoBar
        if InfoBar.instance:
            playing = InfoBar.instance.session.nav.getCurrentlyPlayingServiceReference()
            if playing:
                return playing
            sl = InfoBar.instance.servicelist
            if sl:
                if hasattr(sl, "getCurrent") and callable(sl.getCurrent):
                    return sl.getCurrent()
                if hasattr(sl, "servicelist") and sl.servicelist:
                    return sl.servicelist.getCurrentSelection()
    except Exception as e:
        print("[CiefpEPGinfo] get_current_service error:", e)
    return None


def _epg_event_to_dict(event):
    if not event:
        return None
    if isinstance(event, tuple):
        return {
            "begin": int(event[0]) if len(event) > 0 and event[0] is not None else None,
            "duration": int(event[1]) if len(event) > 1 and event[1] is not None else None,
            "name": str(event[2]) if len(event) > 2 else "",
            "short": str(event[3]) if len(event) > 3 else "",
            "ext": str(event[4]) if len(event) > 4 else "",
        }
    if isinstance(event, dict):
        begin = event.get("begin") or event.get("begin_time") or event.get("start_time")
        duration = event.get("duration") or event.get("dur")
        return {
            "begin": int(begin) if begin else None,
            "duration": int(duration) if duration else None,
            "name": event.get("title") or event.get("name") or "",
            "short": event.get("short_description") or event.get("short") or "",
            "ext": event.get("extended_description") or event.get("description") or event.get("ext") or "",
        }
    try:
        return {
            "begin": int(event.getBeginTime()) if hasattr(event, "getBeginTime") else None,
            "duration": int(event.getDuration()) if hasattr(event, "getDuration") else None,
            "name": event.getEventName() or "",
            "short": event.getShortDescription() or "",
            "ext": event.getExtendedDescription() or "",
        }
    except Exception:
        return None


def get_epg_event_list(max_items=8, service=None):
    # ← IZMENA: sada prima i service (za bouquet mod), ako nije zadat koristi trenutni
    if service is None:
        service = get_current_service()
    if not service:
        return []
    epg = eEPGCache.getInstance()
    out = []
    try:
        cur = epg.lookupEventTime(service, -1, 0)
        cur_d = _epg_event_to_dict(cur)
        if not cur_d or not cur_d.get("name"):
            return []
        out.append(cur_d)
        t = cur_d.get("begin")
        dur = cur_d.get("duration")
        if not t or not dur:
            return out
        next_time = int(t) + int(dur) + 1
        for _ in range(max_items - 1):
            ev = epg.lookupEventTime(service, next_time, 0)
            ev_d = _epg_event_to_dict(ev)
            if not ev_d or not ev_d.get("name"):
                break
            out.append(ev_d)
            b = ev_d.get("begin")
            d = ev_d.get("duration")
            if not b or not d:
                break
            next_time = int(b) + int(d) + 1
    except Exception as e:
        print("[CiefpEPGinfo] get_epg_event_list error:", e)
    return out

# ---------- TITLE TRANSLATION CACHE ----------
_TITLE_TRANSLATION_CACHE = {}


def _translate_title_to_english(title):
    """
    Prevedi naslov na engleski preko GROQ-a.
    """
    if not title:
        return None
    cache_key = title.lower().strip()
    if cache_key in _TITLE_TRANSLATION_CACHE:
        return _TITLE_TRANSLATION_CACHE[cache_key]
    api_key = config.plugins.ciefpepginfo.groq_api_key.value.strip()
    if not api_key:
        print(f"[CiefpEPGinfo] No GROQ key – skipping title translation")
        return None
    try:
        import requests
        if requests is None:
            return None
        ascii_count = sum(1 for c in title if ord(c) < 128)
        is_ascii = (ascii_count / len(title)) > 0.95
        has_non_latin = any(ord(c) > 127 for c in title)
        if is_ascii and not has_non_latin:
            print(f"[CiefpEPGinfo] Title looks English, skipping translation: '{title}'")
            _TITLE_TRANSLATION_CACHE[cache_key] = None
            return None
        payload = {
            "model": config.plugins.ciefpepginfo.groq_model.value,
            "messages": [
                {"role": "system",
                 "content": "You are a translator specialized in movie and TV show titles. "
                            "Translate the following title into English. "
                            "Return ONLY the English title, nothing else. "
                            "Do NOT add quotes, explanations, or extra text. "
                            "If the title is already in English, return it unchanged."},
                {"role": "user", "content": title}
            ],
            "temperature": 0.1,
            "max_tokens": 8000,
        }
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            english_title = data["choices"][0]["message"]["content"].strip()
            english_title = english_title.strip('"').strip("'").strip()
            if english_title.lower().startswith("title:"):
                english_title = english_title[6:].strip()
            print(f"[CiefpEPGinfo] Title translated: '{title}' -> '{english_title}'")
            if english_title.lower().strip() == title.lower().strip():
                _TITLE_TRANSLATION_CACHE[cache_key] = None
                return None
            _TITLE_TRANSLATION_CACHE[cache_key] = english_title
            return english_title
        else:
            print(f"[CiefpEPGinfo] Title translation HTTP {r.status_code}")
            _TITLE_TRANSLATION_CACHE[cache_key] = None
            return None
    except Exception as e:
        print(f"[CiefpEPGinfo] Title translation error: {e}")
        _TITLE_TRANSLATION_CACHE[cache_key] = None
        return None


def _tmdb_search_with_translation(title, year, api_key):
    result, media_type = _tmdb_search_multi(title, year, api_key)
    if result:
        return result, media_type
    english_title = _translate_title_to_english(title)
    if english_title and english_title.lower() != title.lower():
        result, media_type = _tmdb_search_multi(english_title, year, api_key)
        if result:
            return result, media_type
    return None, None

# ---------- GENERIC TITLES ----------
GENERIC_TITLES = {
    "vesti", "vijesti", "dnevnik", "program", "info",
    "informativni program", "jutarnji program", "večernji program",
    "dnevnik 1", "dnevnik 2", "sat", "vreme", "prognoza",
    "report", "reports", "sport", "emisija",
    "razgovor", "intervju", "talk show",
    "news", "weather", "sports", "info", "program",
    "morning show", "evening news", "breaking news",
    "nachrichten", "wetter", "programm",
    "actualités", "météo", "journal",
    "notizie", "meteo", "telegiornale",
    "noticias", "tiempo", "informativos",
    "zprávy", "počasí", "správy", "počasie",
}


def is_generic_title(title):
    if not title:
        return True
    t = title.lower().strip()
    if t in GENERIC_TITLES:
        return True
    if len(t) < 4:
        return True
    return False

# ---------- TMDB ----------
def _tmdb_search_multi(title, year, api_key):
    if not api_key:
        return None, None
    try:
        params = {
            "api_key": api_key,
            "query": title,
            "language": config.plugins.ciefpepginfo.language.value,
            "include_adult": "false",
        }
        if year:
            params["year"] = year
        url = "https://api.themoviedb.org/3/search/multi?" + urllib.parse.urlencode(params)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results = [r for r in data.get("results", []) if r.get("media_type") in ("movie", "tv")]
        if not results:
            return None, None
        if year:
            for c in results:
                c_year = (c.get("release_date") or c.get("first_air_date") or "")[:4]
                if c_year == str(year):
                    return c, c["media_type"]
        best = results[0]
        return best, best["media_type"]
    except Exception as e:
        print("[CiefpEPGinfo] multi search error:", e)
        return None, None

def _tmdb_details(media_id, media_type, api_key):
    try:
        url = (f"https://api.themoviedb.org/3/{media_type}/{media_id}"
               f"?api_key={api_key}&language={config.plugins.ciefpepginfo.language.value}"
               f"&append_to_response=credits,videos")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print("[CiefpEPGinfo] details error:", e)
        return None


# ← IZMENA: _tmdb_trailer je UKLONJEN (trajleri se brišu)

# ---------- TMDB PERSON ----------
def _tmdb_search_person(name, api_key):
    if not api_key:
        return None
    try:
        params = {
            "api_key": api_key,
            "query": name,
            "language": config.plugins.ciefpepginfo.language.value,
        }
        url = "https://api.themoviedb.org/3/search/person?" + urllib.parse.urlencode(params)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results = data.get("results", [])
        return results[0] if results else None
    except Exception as e:
        print("[CiefpEPGinfo] person search error:", e)
        return None


def _tmdb_person_details(person_id, api_key):
    try:
        url = (f"https://api.themoviedb.org/3/person/{person_id}"
               f"?api_key={api_key}"
               f"&language={config.plugins.ciefpepginfo.language.value}"
               f"&append_to_response=movie_credits,tv_credits,external_ids")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print("[CiefpEPGinfo] person details error:", e)
        return None


def _tmdb_person_imdb_rating(person_details, omdb_key):
    if not omdb_key:
        return None
    movie_credits = person_details.get("movie_credits", {}).get("cast", [])
    if not movie_credits:
        return None
    movie_credits.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    top = movie_credits[0]
    title = top.get("title")
    year = (top.get("release_date") or "")[:4]
    if not title:
        return None
    try:
        params = {"apikey": omdb_key, "t": title, "r": "json"}
        if year:
            params["y"] = year
        url = "http://www.omdbapi.com/?" + urllib.parse.urlencode(params)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if data.get("Response") == "True" and data.get("imdbRating") not in ("N/A", ""):
            return data.get("imdbRating")
    except Exception:
        pass
    return None

# ---------- OMDb ----------
def _omdb_rating(media_info, media_type, api_key):
    if not api_key:
        return None
    title = media_info.get("title") if media_type == "movie" else media_info.get("name")
    year = (media_info.get("release_date") or "")[:4] if media_type == "movie" else \
           (media_info.get("first_air_date") or "")[:4]
    if not title:
        return None
    try:
        params = {"apikey": api_key, "t": title, "r": "json"}
        if year:
            params["y"] = year
        url = "http://www.omdbapi.com/?" + urllib.parse.urlencode(params)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if data.get("Response") == "True" and data.get("imdbRating") not in ("N/A", ""):
            return data.get("imdbRating")
    except Exception as e:
        print("[CiefpEPGinfo] omdb error:", e)
    return None

# ---------- TRANSLATION CACHE ----------
_TRANSLATION_CACHE = {}

def _translation_cache_key(text, target_lang):
    import hashlib
    h = hashlib.md5((text + "|" + target_lang).encode("utf-8")).hexdigest()
    return h


def _translate_cached(text, target_lang):
    if not text:
        return text
    key = _translation_cache_key(text, target_lang)
    if key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[key]
    tr = Translator()
    if not tr.is_available():
        print("[CiefpEPGinfo] Translator not available (key or requests missing)")
        return text
    translated = tr.translate(text, target_language=target_lang)
    _TRANSLATION_CACHE[key] = translated
    return translated

# ---------- PLACEHOLDER odabir po žanru ----------
def choose_placeholder(genres):
    if not genres:
        return PLACEHOLDER
    g = " ".join(genres).lower()
    if any(k in g for k in ("sport", "sports")):
        return PLACEHOLDER_SPORT if os.path.exists(PLACEHOLDER_SPORT) else PLACEHOLDER
    if any(k in g for k in ("music", "musical")):
        return PLACEHOLDER_MUSIC if os.path.exists(PLACEHOLDER_MUSIC) else PLACEHOLDER
    if any(k in g for k in ("news", "weather")):
        return PLACEHOLDER_NEWS if os.path.exists(PLACEHOLDER_NEWS) else PLACEHOLDER
    if any(k in g for k in ("animation", "family", "kids")):
        return PLACEHOLDER_KIDS if os.path.exists(PLACEHOLDER_KIDS) else PLACEHOLDER
    if any(k in g for k in ("documentary", "Documentaries")):
        return PLACEHOLDER_DOCU if os.path.exists(PLACEHOLDER_DOCU) else PLACEHOLDER
    return PLACEHOLDER

def _kw_match(combo, keywords):
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', combo):
            return kw
    return None


def detect_non_tmdb(title, description):
    t = (title or "").lower()
    d = (description or "").lower()
    combo = t + " " + d
    print(f"[CiefpDebug] detect_non_tmdb: title='{title}'")
    print(f"[CiefpDebug] combo[:200]='{combo[:200]}'")
    sport_kw = (
        "sport", "sports", "football", "fudbal", "soccer", "nogomet",
        "tennis", "tenis", "basket", "basketball", "košarka", "kosarka",
        "nba", "nfl", "formula 1", "f1", "formula", "formule",
        "moto gp", "motogp", "moto2", "moto3", "olympic", "olimpijada", "olympiáda",
        "atletika", "utakmica", "utakmice", "match", "liga", "extraliga", "kup", "cup",
        "champions league", "premier league", "bundesliga", "serie a", "la liga",
        "weltmeisterschaft", "góly - body - sekundy", "hádzaná", "hadzana", "handball", "rukomet",
        "hokej", "hockey", "lední hokej", "ledni hokej", "volejbal", "volleyball", "odbojka",
        "plavání", "plavani", "swimming", "plivanje", "lyžování", "lyzovani",
        "ski", "skijanje", "cyklistika", "cycling", "biciklizam",
        "závod", "zavod", "race", "utrka", "turnaj", "tournament", "turnir",
    )
    music_kw = (
        "music", "musical", "muzika", "glazba", "hudba", "concert", "koncert", "live concert",
        "festival", "mtv", "vh1", "muzike", "opera", "opereta",
    )
    news_kw = (
        "news", "vesti", "novosti", "nachrichten", "actualités", "actualites", "noticias",
        "telegiornale", "dnevnik", "tagesschau", "správy", "spravy", "zprávy", "zpravy",
        "reportáž", "reportaz", "newstime", "jutarnji program", "informativni", "program",
    )
    kids_kw = (
        "kids", "dečiji", "za decu", "for kids", "children's", "child's", "kinder",
        "infantile", "pour enfants", "per bambini", "para niños", "детский", "çocuk", "παιδικός",
    )
    documentary_kw = (
        "documentary", "dokument", "dokumentarni", "dokumentárního",
        "dokumentární", "dokumentarni", "dokumentarna",
    )
    hit = _kw_match(combo, sport_kw)
    if hit:
        print(f"[CiefpDebug] SPORT hit: '{hit}'")
        return True, PLACEHOLDER_SPORT if os.path.exists(PLACEHOLDER_SPORT) else PLACEHOLDER
    hit = _kw_match(combo, music_kw)
    if hit:
        print(f"[CiefpDebug] MUSIC hit: '{hit}'")
        return True, PLACEHOLDER_MUSIC if os.path.exists(PLACEHOLDER_MUSIC) else PLACEHOLDER
    hit = _kw_match(combo, news_kw)
    if hit:
        print(f"[CiefpDebug] NEWS hit: '{hit}'")
        return True, PLACEHOLDER_NEWS if os.path.exists(PLACEHOLDER_NEWS) else PLACEHOLDER
    hit = _kw_match(combo, kids_kw)
    if hit:
        print(f"[CiefpDebug] KIDS hit: '{hit}'")
        return True, PLACEHOLDER_KIDS if os.path.exists(PLACEHOLDER_KIDS) else PLACEHOLDER
    hit = _kw_match(combo, documentary_kw)
    if hit:
        print(f"[CiefpDebug] DOCU hit: '{hit}'")
        return True, PLACEHOLDER_DOCU if os.path.exists(PLACEHOLDER_DOCU) else PLACEHOLDER
    return False, None
# ---------- ← NOVO: USER BOUQUETS (prekopirano iz CiefpE2editor) ----------
ENIGMA2_DIR = "/etc/enigma2"
BOUQUETS_TV_FILE = "/etc/enigma2/bouquets.tv"


def load_all_bouquets_data():
    """
    Prekopirano iz CiefpE2editor.load_all_bouquets().
    Vraća:
      bouquet_names: dict {display_name: bouquet_file}
      bouquet_order: list[display_name]  (redosled kao u Enigma2)
    """
    bouquet_names = {}
    bouquet_files = {}
    bouquet_order_list = []

    if not os.path.exists(BOUQUETS_TV_FILE):
        print(f"[CiefpEPGinfo] bouquets.tv not found: {BOUQUETS_TV_FILE}")
        return bouquet_names, bouquet_order_list

    # 1) Pročitaj redosled fajlova iz bouquets.tv
    bouquet_order = []
    try:
        with open(BOUQUETS_TV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if "FROM BOUQUET" in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    if start != -1 and end != -1:
                        bouquet_order.append(line[start:end])
    except Exception as e:
        print(f"[CiefpEPGinfo] Error reading bouquets.tv: {e}")
        return bouquet_names, bouquet_order_list

    print(f"[CiefpEPGinfo] Found {len(bouquet_order)} entries in bouquets.tv")

    # 2) Za svaki fajl pročitaj #NAME
    for bouquet_file in bouquet_order:
        file_path = os.path.join(ENIGMA2_DIR, bouquet_file)
        if not os.path.exists(file_path):
            print(f"[CiefpEPGinfo] Bouquet file missing: {file_path}")
            continue
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if first_line.startswith("#NAME"):
                    display_name = first_line.replace("#NAME", "", 1).strip()
                    bouquet_names[display_name] = bouquet_file
                    bouquet_files[bouquet_file] = display_name
                    bouquet_order_list.append(display_name)
        except Exception as e:
            print(f"[CiefpEPGinfo] Error reading bouquet {bouquet_file}: {e}")

    print(f"[CiefpEPGinfo] Loaded {len(bouquet_names)} bouquets")
    return bouquet_names, bouquet_order_list


def load_bouquet_channels_data(bouquet_file, lamedb_services):
    """
    Prekopirano iz CiefpE2editor.load_bouquet_channels().
    Vraća:
      channel_list: list[display_name]   (ono što ide u MenuList)
      channel_refs: dict {display_name: raw_ref_string}
                    gde je raw_ref_string cela '#SERVICE ...' linija
                    (isto kao u CiefpE2editor — string, ne eServiceReference)
    """
    channel_refs = {}
    channel_list = []
    bouquet_path = os.path.join(ENIGMA2_DIR, bouquet_file)
    if not os.path.exists(bouquet_path):
        print(f"[CiefpEPGinfo] Bouquet file not found: {bouquet_path}")
        return channel_list, channel_refs

    try:
        with open(bouquet_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            if line.startswith("#NAME"):
                i += 1
                continue

            elif line.startswith("#SERVICE"):
                # StreamRelay
                if "http%3a//0.0.0.0%3a9999/" in line or "%3a9999" in line:
                    channel_name = "Unknown StreamRelay"
                    url_parts = line.split(":")
                    if len(url_parts) >= 11 and url_parts[10] and not url_parts[10].startswith("http"):
                        channel_name = url_parts[10]
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("#DESCRIPTION"):
                        desc_line = lines[i + 1].strip()
                        channel_name = desc_line.replace("#DESCRIPTION", "").strip()
                        i += 1
                    display_name = f"{channel_name} (StreamRelay)"
                    channel_list.append(display_name)
                    channel_refs[display_name] = line
                    i += 1
                    continue

                # IPTV
                elif (line.startswith("#SERVICE 4097:")
                      or line.startswith("#SERVICE 5001:")
                      or line.startswith("#SERVICE 5002:")
                      or "http" in line.lower()):
                    channel_name = "Unknown IPTV"
                    url_parts = line.split(":")
                    if len(url_parts) >= 11 and url_parts[10]:
                        channel_name = url_parts[10]
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("#DESCRIPTION"):
                        desc_line = lines[i + 1].strip()
                        channel_name = desc_line.replace("#DESCRIPTION", "").strip()
                        i += 1
                    display_name = f"{channel_name} (IPTV)"
                    channel_list.append(display_name)
                    channel_refs[display_name] = line
                    i += 1
                    continue

                else:
                    parts = line.split(":")
                    if len(parts) >= 10:
                        # Marker (1:64:)
                        if parts[1] == "64":
                            if i + 1 < len(lines) and lines[i + 1].strip().startswith("#DESCRIPTION"):
                                marker_name = lines[i + 1].strip().replace("#DESCRIPTION", "").strip()
                                display_marker = f"[{marker_name}]"
                                channel_list.append(display_marker)
                                channel_refs[display_marker] = line
                                i += 2
                                continue
                            i += 1
                            continue

                        # Običan DVB servis
                        sid = parts[3]
                        tsid = parts[4]
                        onid = parts[5]
                        satfreq = parts[6].lower()
                        satfreq = f"00{satfreq}" if len(satfreq) == 6 else satfreq.zfill(8)

                        search_keys = [
                            f"{int(sid, 16):04x}:{satfreq}:{int(tsid, 16):04x}:{int(onid, 16):04x}",
                            f"{sid.lower()}:{satfreq}:{tsid.lower()}:{onid.lower()}",
                        ]
                        channel_name = None
                        for search_key in search_keys:
                            channel_name = lamedb_services.get(search_key)
                            if channel_name:
                                break
                        if not channel_name:
                            channel_name = f"Unknown ({search_keys[0]})"

                        channel_list.append(channel_name)
                        channel_refs[channel_name] = line
                    i += 1

            elif line.startswith("#DESCRIPTION"):
                marker_name = line.replace("#DESCRIPTION", "").strip()
                display_marker = f"[{marker_name}]"
                if display_marker not in channel_list:
                    channel_list.append(display_marker)
                    channel_refs[display_marker] = "#SERVICE 1:64:0:0:0:0:0:0:0:0:"
                i += 1
            else:
                i += 1

    except Exception as e:
        print(f"[CiefpEPGinfo] Error loading bouquet channels: {e}")

    return channel_list, channel_refs


def parse_lamedb_simple():
    """
    Pojednostavljena verzija parse_lamedb iz CiefpE2editor.
    Vraća dict {key: name} za DVB servise – potrebno za load_bouquet_channels_data.
    """
    lamedb_path = "/etc/enigma2/lamedb"
    services = {}
    if not os.path.exists(lamedb_path):
        return services
    try:
        with open(lamedb_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        start_idx = content.find("\nservices\n")
        end_idx = content.find("\nend\n", start_idx)
        if start_idx == -1 or end_idx == -1:
            return services
        services_block = content[start_idx + 10:end_idx]
        lines = services_block.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if ":" in line and not line.startswith("p:") and not line.startswith("c:"):
                parts = line.split(":")
                if len(parts) >= 5:
                    sid = parts[0]
                    satfreq = parts[1].lower()
                    tsid = parts[2]
                    onid = parts[3]
                    key1 = f"{sid}:{satfreq}:{tsid}:{onid}"
                    key2 = f"{sid.lstrip('0') or '0'}:{satfreq}:{tsid.lstrip('0') or '0'}:{onid.lstrip('0') or '0'}"
                    name = ""
                    if i + 1 < len(lines):
                        name = lines[i + 1].strip()
                    if name and not name.startswith("p:") and not name.startswith("c:"):
                        services[key1] = name
                        services[key2] = name
                    i += 2
                    continue
            i += 1
    except Exception as e:
        print(f"[CiefpEPGinfo] parse_lamedb_simple error: {e}")
    return services


def raw_ref_to_eServiceReference(raw_line):
    """
    Pretvara '#SERVICE 1:0:19:...' string u eServiceReference.
    Vraća None ako ne uspe (npr. IPTV URL stream).
    """
    if not raw_line:
        return None
    ref_str = raw_line.strip()
    if ref_str.startswith("#SERVICE"):
        ref_str = ref_str[9:].strip()
    if not ref_str:
        return None
    # IPTV / StreamRelay – ne mogu preko eServiceReference
    if (ref_str.startswith("4097:")
            or ref_str.startswith("5001:")
            or ref_str.startswith("5002:")
            or "http" in ref_str.lower()):
        return None
    try:
        ref = eServiceReference(ref_str)
        if ref.valid():
            return ref
    except Exception as e:
        print(f"[CiefpEPGinfo] raw_ref_to_eServiceReference error: {e}")
    return None


def get_service_name_from_ref(ref):
    """Vraća ime kanala iz eServiceReference"""
    try:
        service = eServiceCenter.getInstance().info(ref)
        if service:
            name = service.getName(ref)
            if name:
                return name
    except Exception:
        pass
    try:
        name = ref.getName()
        if name:
            return name
    except Exception:
        pass
    return "Unknown"


# ---------- MAIN SCREEN ----------
class CiefpEPGinfoMain(Screen):
    skin = """
        <screen name="CiefpEPGinfoMain" position="0,0" size="1920,1080"
                backgroundColor="#011a2e">

            <widget name="picon" position="40,40" size="220,140" alphatest="blend" zPosition="2"/>

            <widget name="day" position="500,40" size="200,40" font="Regular;30"
                    foregroundColor="#00BFFF" backgroundColor="#011a2e" transparent="1" halign="left"/>
            <widget name="date" position="500,100" size="200,40" font="Regular;30"
                    foregroundColor="#00BFFF" backgroundColor="#011a2e" transparent="1" halign="left"/>

            <widget name="clock" position="290,40" size="200,100" font="Regular;80"
                    foregroundColor="#FFFFFF" backgroundColor="#011a2e" transparent="1" halign="left"/>

            <widget name="service_name" position="40,200" size="600,50" font="Regular;36"
                    foregroundColor="#FFFFFF" backgroundColor="#011a2e" transparent="1"/>

            <widget name="epg_list" position="30,260" size="610,720"
                    scrollbarMode="showOnDemand" itemHeight="40" font="Regular;26" backgroundColor="#011a2e"/>

            <widget name="title" position="680,40" size="900,50" font="Regular;38"
                    foregroundColor="#FFFFFF" backgroundColor="#011a2e" transparent="1"/>

            <widget name="epg_title" position="680,95" size="900,35" font="Regular;24"
                    foregroundColor="#A0A0A0" backgroundColor="#011a2e" transparent="1"/>

            <widget name="duration" position="680,140" size="300,35" font="Regular;26"
                    foregroundColor="#D3D3D3" backgroundColor="#011a2e" transparent="1"/>
            <widget name="rating" position="680,180" size="300,35" font="Regular;26"
                    foregroundColor="#03a81f" backgroundColor="#011a2e" transparent="1"/>
            <widget name="imdb_rating" position="680,220" size="300,35" font="Regular;26"
                    foregroundColor="#F5C518" backgroundColor="#011a2e" transparent="1"/>

            <widget name="genres" position="680,260" size="600,35" font="Regular;26"
                    foregroundColor="#f702db" backgroundColor="#011a2e" transparent="1"/>

            <widget name="director" position="680,300" size="900,35" font="Regular;26"
                    foregroundColor="#f79102" backgroundColor="#011a2e" transparent="1"/>

            <widget name="plot" position="680,340" size="600,576" font="Regular;24"
                    foregroundColor="#FFFFFF" backgroundColor="#011a2e" transparent="1" valign="top"/>

            <widget name="cast_header" position="680,800" size="300,30" font="Regular;24"
                    foregroundColor="#00FFFF" backgroundColor="#011a2e" transparent="1"/>

            <widget name="cast_col1" position="680,850" size="510,280" font="Regular;20"
                    foregroundColor="#00FFFF" backgroundColor="#011a2e" transparent="1" valign="top"/>

            <widget name="cast_col2" position="1200,850" size="510,280" font="Regular;20"
                    foregroundColor="#00FFFF" backgroundColor="#011a2e" transparent="1" valign="top"/>

            <widget name="poster" position="1300,40" size="500,750" alphatest="blend" zPosition="2"/>

            <widget name="status" position="1280,1010" size="820,40" font="Regular;22"
                    foregroundColor="#00FF00" backgroundColor="#011a2e" transparent="1" halign="left"/>

            <ePixmap pixmap="buttons/red.png" position="0,1010" size="35,35" alphatest="blend"/>
            <eLabel text="Exit" position="50,1010" size="180,40" font="Regular;26"
                    foregroundColor="white" backgroundColor="#800000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/green.png" position="240,1010" size="35,35" alphatest="blend"/>
            <eLabel text="Filmography" position="290,1010" size="180,40" font="Regular;26"
                    foregroundColor="white" backgroundColor="#008000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/yellow.png" position="480,1010" size="35,35" alphatest="blend"/>
            <eLabel text="Cast explore" position="530,1010" size="220,40" font="Regular;26"
                    foregroundColor="white" backgroundColor="#808000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/blue.png" position="760,1010" size="35,35" alphatest="blend"/>
            <eLabel text="Bouquets" position="810,1010" size="180,40" font="Regular;26"
                    foregroundColor="white" backgroundColor="#000080" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/red.png" position="1000,1010" size="35,35" alphatest="blend"/>
            <eLabel text="Info:Settings" position="1050,1010" size="220,40" font="Regular;26"
                    foregroundColor="white" backgroundColor="#960396" halign="center" valign="center"/>
        </screen>
    """.format(version=PLUGIN_VERSION)

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["picon"] = Pixmap()
        self["day"] = Label("")
        self["date"] = Label("")
        self["clock"] = Label("")
        self["service_name"] = Label("")
        self["epg_list"] = MenuList([])
        self["title"] = Label("")
        self["epg_title"] = Label("")
        self["duration"] = Label("")
        self["rating"] = Label("")
        self["imdb_rating"] = Label("")
        self["genres"] = Label("")
        self["director"] = Label("")
        self["plot"] = Label("")
        self["cast_header"] = Label("")
        self["cast_col1"] = Label("")
        self["cast_col2"] = Label("")
        self["poster"] = Pixmap()
        self["status"] = Label("Ready")

        self.epg_events = []
        self.current_event = None
        self.current_media_details = None
        self.current_media_type = None
        # ← IZMENA: current_trailer_id uklonjen (trajleri se brišu)
        self._picon_cache = {}
        self.picon_manager = None

        # ← NOVO: bouquet mod state
        self.bouquet_mode = False
        self.bouquet_names = {}          # {display_name: bouquet_file}
        self.bouquet_order = []          # list[display_name] (redosled)
        self.bouquet_channels = []       # list[display_name] – trenutni buket
        self.bouquet_channel_refs = {}   # {display_name: raw_ref_string}
        self.bouquet_name = ""
        self.current_bouquet_display = None
        self.current_bouquet_ref = None  # eServiceReference odabranog kanala (za EPG)
        self._epg_bouquet_ref = None
        self._lamedb_cache = None

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "MenuActions", "InfoActions"],
            {
                "cancel": self.keyBack,
                "red": self.close,
                "green": self.filmography_browser,
                "yellow": self.cast_explore,
                "blue": self.open_bouquets,          # ← IZMENA: bilo open_settings
                "ok": self.on_ok,
                "up": self.on_up,
                "down": self.on_down,
                "left": self.on_up,
                "right": self.on_down,
                "menu": self.open_settings,
                "info": self.open_settings,          # ← IZMENA: bilo show_trailer
            }, -1)

        self.clock_timer = eTimer()
        self.clock_timer.callback.append(self._update_clock)
        self.clock_timer.start(1000)

        self.epg_refresh_timer = eTimer()
        self.epg_refresh_timer.callback.append(self._refresh_timer_cb)  # ← IZMENA
        self.epg_refresh_timer.start(60000)

        self.onLayoutFinish.append(self.on_start)
        self.onClose.append(self.__onClose)
        self._saved_media_state = None

        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.command_finished)
        self.container.dataAvail.append(self.version_data_avail)
        self.version_check_in_progress = False
        self.version_buffer = b''
        self.onLayoutFinish.append(self.check_for_updates)

    def __onClose(self):
        try:
            self.clock_timer.stop()
        except Exception:
            pass
        try:
            self.epg_refresh_timer.stop()
        except Exception:
            pass
        try:
            if "actions" in self:
                self["actions"].destroy()
                del self["actions"]
        except Exception:
            pass

    # ---------- START ----------
    def on_start(self):
        self._init_picon_manager()
        self._show_default_poster()
        self._update_clock()
        self.refresh_epg()

    def _update_clock(self):
        now = datetime.now()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self["day"].setText(days[now.weekday()])
        self["date"].setText(f"{now.day}. {months[now.month-1]}")
        self["clock"].setText(now.strftime("%H:%M"))

    def _show_default_poster(self):
        px = load_pixmap_safe(PLACEHOLDER)
        if px and self["poster"].instance:
            self["poster"].instance.setPixmap(px)

    # ← NOVO: timer callback – samo osveži EPG ako nismo u bouquet modu
    def _refresh_timer_cb(self):
        if self.bouquet_mode:
            return  # u bouquet modu ne diramo listu automatski
        self.refresh_epg()

    # ---------- Update plugin ------------
    def check_for_updates(self):
        if self.version_check_in_progress:
            return
        self.version_check_in_progress = True
        self["status"].setText("Checking for updates...")
        try:
            self.container.execute(f"wget -q --timeout=10 -O - {VERSION_URL}")
        except Exception as e:
            self.version_check_in_progress = False
            self["status"].setText("Update check failed.")
            print("[CiefpEPGinfo] Update error:", e)

    def version_data_avail(self, data):
        self.version_buffer += data

    def command_finished(self, retval):
        if self.version_check_in_progress:
            self.version_check_closed(retval)
        else:
            self.update_completed(retval)

    def version_check_closed(self, retval):
        self.version_check_in_progress = False
        if retval == 0:
            try:
                remote_version = self.version_buffer.decode().strip()
                self.version_buffer = b''
                print(f"[CiefpEPGinfo] Local: {PLUGIN_VERSION}, Remote: {remote_version}")
                if remote_version != PLUGIN_VERSION:
                    self.session.openWithCallback(
                        self.start_update,
                        MessageBox,
                        f"New version: v{remote_version}\nInstall now?",
                        MessageBox.TYPE_YESNO
                    )
                else:
                    self["status"].setText("The plugin is up to date.")
            except Exception as e:
                self["status"].setText("Version check failed.")
                print(f"[CiefpEPGinfo] Parse error: {e}")
        else:
            self["status"].setText("Update check failed.")

    def start_update(self, answer):
        if not answer:
            self["status"].setText("Update cancelled.")
            return
        self["status"].setText("Updating...")
        self.container.execute(UPDATE_COMMAND)

    def update_completed(self, retval):
        if retval == 0:
            self["status"].setText("Update OK! Restarting...")
            self.container.execute("sleep 2 && killall -9 enigma2")
        else:
            self["status"].setText("Update failed.")

    # ---------- SERVICE INFO ----------
    def _get_service_name(self):
        try:
            svc = self.session.nav.getCurrentService()
            if svc:
                info = svc.info()
                name = info.getName()
                if name:
                    return name
        except Exception:
            pass
        return "Unknown Channel"

    def _init_picon_manager(self):
        possible_paths = [
            "/picon/",
            "/media/usb/picon/",
            "/media/hdd/picon/",
            "/usr/share/enigma2/picon/",
        ]
        picon_path = None
        for p in possible_paths:
            if os.path.exists(p):
                picon_path = p
                break
        if not picon_path:
            picon_path = "/picon/"
        self.picon_manager = PiconManager(picon_path)
        print(f"[CiefpEPGinfo] PiconManager initialized with path: {picon_path}")
        print(f"[CiefpEPGinfo] Search dirs: {self.picon_manager.search_dirs}")

    # ← IZMENA: _load_picon sada prima i ref (za bouquet mod)
    def _load_picon(self, ref=None):
        try:
            if ref is None:
                ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if not ref:
                self["picon"].hide()
                return
            ref_str = ref.toString()
            channel_name = get_service_name_from_ref(ref)
            print(f"[CiefpDebug] ref_str = {ref_str}")
            print(f"[CiefpDebug] channel_name = {channel_name}")
            if self.picon_manager:
                picon_file = self.picon_manager.find_picon(ref_str, channel_name)
                if picon_file:
                    px = LoadPixmap(picon_file)
                    if px and self["picon"].instance:
                        self["picon"].instance.setPixmap(px)
                        self["picon"].show()
                        print(f"[CiefpEPGinfo] Picon loaded: {picon_file}")
                        return
            self["picon"].hide()
        except Exception as e:
            print(f"[CiefpEPGinfo] _load_picon error: {e}")
            try:
                self["picon"].hide()
            except Exception:
                pass

    def _find_picon_by_reference(self, folder, ref_str):
        if not os.path.isdir(folder):
            return None
        ref_clean = ref_str.strip().rstrip(":")
        candidates = [
            ref_clean.replace(":", "_") + ".png",
            ref_clean.replace(":", "_") + ".jpg",
            ref_clean.replace(":", "").replace(" ", "") + ".png",
        ]
        candidates += [c.lower() for c in candidates if c.lower() not in candidates]
        for name in candidates:
            path = os.path.join(folder, name)
            if os.path.exists(path):
                return path
        return None

    def _find_picon_by_name(self, folder, channel_name):
        if not os.path.isdir(folder) or not channel_name:
            return None
        clean = channel_name.strip()
        for suffix in [" (IPTV)", " (StreamRelay)", " (HD)", " (SD)", " HD", " SD",
                       " HD)", " (HD", " FHD", " UHD", " 4K"]:
            if clean.lower().endswith(suffix.lower()):
                clean = clean[:-len(suffix)]
        clean = clean.strip()
        if not clean:
            return None
        lower = clean.lower()
        variants = [
            lower, lower.replace(" ", ""), lower.replace(" ", "_"),
            lower.replace(" ", "-"), lower.replace("&", "and"),
            lower.replace("+", "plus"), lower.replace(".", ""),
            lower.replace("'", ""), lower.replace(":", ""),
        ]
        variants = list(dict.fromkeys(variants))
        extensions = [".png", ".jpg", ".jpeg"]
        for name in variants:
            for ext in extensions:
                path = os.path.join(folder, name + ext)
                if os.path.exists(path):
                    return path
            for ext in extensions:
                path = os.path.join(folder, clean + ext)
                if os.path.exists(path):
                    return path
        return None

    def _show_picon(self, path):
        try:
            px = LoadPixmap(path)
            if px and self["picon"].instance:
                self["picon"].instance.setPixmap(px)
                self["picon"].show()
                return True
        except Exception as e:
            print(f"[CiefpEPGinfo] _show_picon error: {e}")
        return False

    # ---------- ← NOVO: USER BOUQUETS ----------
    def open_bouquets(self):
        """Plavo dugme – ChoiceBox sa listom user buketa (kao CiefpE2editor)"""
        self["status"].setText("Loading bouquets...")

        # Uvek osveži listu (korisnik može da doda novi buket u Enigma2)
        self.bouquet_names, self.bouquet_order = load_all_bouquets_data()

        if not self.bouquet_order:
            self["status"].setText("No user bouquets found")
            self.session.open(
                MessageBox,
                "No user bouquets found in /etc/enigma2/bouquets.tv\n\n"
                "Proveri da li imaš bukete u Enigma2 servisnoj listi.",
                MessageBox.TYPE_INFO, timeout=5
            )
            return

        menu = []
        if self.bouquet_mode:
            menu.append(("← Back to current channel EPG", "BACK"))
            menu.append(("─" * 30, None))

        for name in self.bouquet_order:
            menu.append((name, name))

        def cb(choice):
            if not choice:
                return
            action = choice[1]
            if action is None:
                return
            if action == "BACK":
                self._exit_bouquet_mode()
                return
            # action = display_name
            bouquet_file = self.bouquet_names.get(action)
            if bouquet_file:
                self._enter_bouquet_mode(action, bouquet_file)

        self.session.openWithCallback(
            cb, ChoiceBox,
            title="User Bouquets",
            list=menu
        )

    def _enter_bouquet_mode(self, display_name, bouquet_file):
        """Učitaj kanale iz buketa u levu listu"""
        self["status"].setText(f"Loading bouquet: {display_name}...")

        # Keširaj lamedb (da ne čitamo svaki put)
        if self._lamedb_cache is None:
            self._lamedb_cache = parse_lamedb_simple()

        channels, refs = load_bouquet_channels_data(bouquet_file, self._lamedb_cache)

        if not channels:
            self["status"].setText(f"Bouquet '{display_name}' is empty")
            return

        self.bouquet_mode = True
        self.bouquet_name = display_name
        self.current_bouquet_display = display_name
        self.bouquet_channels = channels
        self.bouquet_channel_refs = refs

        self["service_name"].setText(f"📺 {display_name}")

        # Napuni MenuList
        menu_items = []
        for idx, ch_name in enumerate(channels):
            display = ch_name
            if len(display) > 55:
                display = display[:55] + "…"
            menu_items.append(f"  {idx + 1}. {display}")
        self["epg_list"].setList(menu_items)
        self["epg_list"].moveToIndex(0)

        # Nađi prvi pravi kanal (preskoči markere)
        first_idx = self._find_first_real_channel(0)
        self["epg_list"].moveToIndex(first_idx)
        self._on_bouquet_channel_changed(first_idx)
        self["status"].setText(f"Bouquet: {display_name}  (OK = play, BACK = exit)")

    def _find_first_real_channel(self, start_idx=0):
        """Vraća indeks prvog pravog kanala (ne markera) od start_idx."""
        for i in range(start_idx, len(self.bouquet_channels)):
            raw = self.bouquet_channel_refs.get(self.bouquet_channels[i], "")
            if raw and "1:64:" not in raw and not self.bouquet_channels[i].startswith("["):
                return i
        return start_idx  # fallback

    def _exit_bouquet_mode(self):
        """Vrati se na normalni EPG mod (trenutni kanal)"""
        self.bouquet_mode = False
        self.bouquet_name = ""
        self.bouquet_channels = []
        self.bouquet_channel_refs = {}
        self.current_bouquet_display = None
        self.current_bouquet_ref = None
        self._epg_bouquet_ref = None
        self["status"].setText("Back to current channel")
        self.refresh_epg()

    def _load_bouquet_channel_epg(self, display_name):
        """
        Učitaj EPG za kanal iz buketa.
        - Ako je DVB servis → eServiceReference → eEPGCache lookup
        - Ako je IPTV/StreamRelay → nema EPG, ali pokušaj TMDB po imenu kanala
        """
        raw_ref = self.bouquet_channel_refs.get(display_name)
        if not raw_ref:
            return

        self.current_bouquet_display = display_name

        ref = raw_ref_to_eServiceReference(raw_ref)

        # Ažuriraj ime kanala u zaglavlju
        self["service_name"].setText(f"📺 {self.bouquet_name} – {display_name}")

        # Picon – samo za DVB
        if ref:
            self._load_picon(ref)
        else:
            self["picon"].hide()

        # EPG lookup
        if ref:
            self._epg_bouquet_ref = ref
            self.epg_events = get_epg_event_list(max_items=12, service=ref)
        else:
            # IPTV / StreamRelay – nema EPG
            self._epg_bouquet_ref = None
            self.epg_events = []

        if not self.epg_events:
            # Nema EPG – prikaži ime kanala + pokušaj TMDB po imenu kanala
            self["title"].setText(display_name)
            self["epg_title"].setText("EPG: no data")
            self["duration"].setText("")
            self["rating"].setText("")
            self["imdb_rating"].setText("")
            self["genres"].setText("")
            self["director"].setText("")
            self["plot"].setText("No EPG data for this channel.")
            self["cast_header"].setText("")
            self["cast_col1"].setText("")
            self["cast_col2"].setText("")
            self._set_poster(PLACEHOLDER)
            self.current_media_details = None
            self.current_media_type = None
            self.current_event = None

            # Opcioni TMDB lookup po imenu kanala
            api_key = config.plugins.ciefpepginfo.tmdb_api_key.value.strip()
            clean_ch = re.sub(r"\s*\((IPTV|StreamRelay)\)\s*$", "", display_name).strip()
            if api_key and clean_ch and not is_generic_title(clean_ch):
                threading.Thread(
                    target=self._fetch_tmdb_async,
                    args=(clean_ch, None, api_key, ""),
                    daemon=True
                ).start()
            return

        # Ima EPG – obradi prvi događaj
        self.current_event = self.epg_events[0]
        self._process_event(self.current_event, is_current=True)

    def _on_bouquet_channel_changed(self, idx):
        """Korisnik je promenio kanal gore/dole – učitaj EPG za njega.
        Markeri (#SERVICE 1:64:) se preskaču – ostaje prethodni kanal.
        """
        if not self.bouquet_mode:
            return
        if not (0 <= idx < len(self.bouquet_channels)):
            return

        display_name = self.bouquet_channels[idx]
        raw_ref = self.bouquet_channel_refs.get(display_name, "")

        # Preskoči markere i prazne unose – ne diraj trenutni prikaz
        if not raw_ref or "1:64:" in raw_ref or display_name.startswith("["):
            self["status"].setText(f"Marker: {display_name}  (nije kanal)")
            return

        self._load_bouquet_channel_epg(display_name)

    # ---------- EPG ----------
    def refresh_epg(self):
        """Ponovo učitaj EPG listu i ažuriraj UI (normalni mod)"""
        if self.bouquet_mode:
            return  # u bouquet modu ne diramo
        self["status"].setText("Loading EPG...")
        self.epg_events = get_epg_event_list(max_items=12)
        self["service_name"].setText(self._get_service_name())
        self._load_picon()

        if not self.epg_events:
            self["epg_list"].setList(["No EPG data available"])
            self["status"].setText("No EPG data")
            return

        menu_items = []
        for idx, ev in enumerate(self.epg_events):
            begin = ev.get("begin")
            if begin:
                try:
                    hhmm = time.strftime("%H:%M", time.localtime(int(begin)))
                except Exception:
                    hhmm = "--:--"
            else:
                hhmm = "--:--"
            try:
                if begin:
                    day_short = time.strftime("%a", time.localtime(int(begin)))
                else:
                    day_short = ""
            except Exception:
                day_short = ""
            try:
                if begin:
                    date_short = time.strftime("%d. %b", time.localtime(int(begin)))
                else:
                    date_short = ""
            except Exception:
                date_short = ""
            name = ev.get("name", "")
            if len(name) > 55:
                name = name[:55] + "…"
            if idx == 0:
                prefix = "▶"
            else:
                prefix = "  "
            item_text = f"{prefix} {day_short} {date_short}  {hhmm}  {name}"
            menu_items.append(item_text)

        self["epg_list"].setList(menu_items)
        self.current_event = self.epg_events[0]
        self["epg_list"].moveToIndex(0)
        self._process_event(self.current_event, is_current=True)

    def _process_event(self, event, is_current=False):
        """Obradi jedan EPG događaj – prikaži detalje (i TMDB ako treba)"""
        if not event:
            return

        raw_title = event.get("name", "")
        short = event.get("short", "")
        ext = event.get("ext", "")
        description = (short + " " + ext).strip()

        title = re.sub(r"\s*\[.*?\]|\s*\(.*?\)|\s*-\s*.+$", "", raw_title).strip()
        title = re.sub(r"^Film[:\-]?\s*|^Movie[:\-]?\s*", "", title, flags=re.I).strip()

        year = None
        m = re.search(r"\b(19|20)\d{2}\b", raw_title + " " + description)
        if m:
            year = int(m.group(0))

        self["title"].setText(title or raw_title)
        self["epg_title"].setText(f"EPG: {raw_title}")

        dur = event.get("duration")
        if dur:
            minutes = int(dur) // 60
            self["duration"].setText(f"Duration: {minutes} min (EPG)")
        else:
            self["duration"].setText("Duration: N/A")

        self["rating"].setText("")
        self["imdb_rating"].setText("")
        self["genres"].setText("")
        self["director"].setText("")
        # ← IZMENA: current_trailer_id uklonjen
        self.current_media_details = None
        self.current_media_type = None

        if description:
            if len(description) > 750:
                cut = description[:750].rfind(". ")
                if cut > 400:
                    description = description[:cut + 1] + " ..."
                else:
                    description = description[:750] + " ..."
            self["plot"].setText("Plot:\n" + description)
        else:
            self["plot"].setText("Plot:\nNo description available.")

        self["cast_header"].setText("")
        self["cast_col1"].setText("")
        self["cast_col2"].setText("")

        print(f"[CiefpDebug] ===== PROCESS EVENT =====")
        print(f"[CiefpDebug] raw_title = '{raw_title}'")
        print(f"[CiefpDebug] cleaned title = '{title}'")
        print(f"[CiefpDebug] year = {year}")
        print(f"[CiefpDebug] description[:100] = '{description[:100]}'")
        api_key = config.plugins.ciefpepginfo.tmdb_api_key.value.strip()
        if api_key and not is_generic_title(title):
            self["status"].setText(f"Searching TMDB: {title}" + (f" ({year})" if year else ""))
            threading.Thread(
                target=self._fetch_tmdb_async,
                args=(title, year, api_key, description),
                daemon=True
            ).start()
            return

        print(f"[CiefpDebug] Skipping TMDB (generic or no key): '{title}'")
        self["status"].setText("Non-TMDB content (EPG only)")
        non_tmdb, placeholder = detect_non_tmdb(title, description)
        if non_tmdb:
            self._set_poster(placeholder)
        else:
            self._set_poster(PLACEHOLDER)

        if (config.plugins.ciefpepginfo.translate_epg.value
                and config.plugins.ciefpepginfo.translate_epg_description.value
                and config.plugins.ciefpepginfo.groq_api_key.value.strip()):
            target = config.plugins.ciefpepginfo.translate_to.value
            threading.Thread(
                target=self._translate_description_async,
                args=(description, target),
                daemon=True
            ).start()
        return

    def _fetch_tmdb_async(self, title, year, api_key, epg_description):
        try:
            result, media_type = _tmdb_search_with_translation(title, year, api_key)
            if not result:
                print(f"[CiefpEPGinfo] TMDB not found: {title}")
                self._fallback_to_epg(title, epg_description, "Not found on TMDB")
                return
            media_id = result.get("id")
            details = _tmdb_details(media_id, media_type, api_key)
            if not details:
                self._fallback_to_epg(title, epg_description, "TMDB details error")
                return
            self.current_media_details = details
            self.current_media_type = media_type
            self._update_ui_with_tmdb(details, media_type)

            overview = (details.get("overview") or "").strip()
            if not overview and epg_description:
                if (config.plugins.ciefpepginfo.translate_epg.value
                        and config.plugins.ciefpepginfo.translate_epg_description.value
                        and config.plugins.ciefpepginfo.groq_api_key.value.strip()):
                    target = config.plugins.ciefpepginfo.translate_to.value
                    threading.Thread(
                        target=self._translate_description_async,
                        args=(epg_description, target),
                        daemon=True
                    ).start()
        except Exception as e:
            print("[CiefpEPGinfo] fetch_tmdb_async error:", e)
            self._fallback_to_epg(title, epg_description, "TMDB fetch error")

    def _fallback_to_epg(self, title, description, reason="Fallback"):
        self["status"].setText(f"{reason} – EPG only")
        non_tmdb, placeholder = detect_non_tmdb(title, description)
        if non_tmdb:
            print(f"[CiefpEPGinfo] detect_non_tmdb hit for: {title}")
            self._set_poster(placeholder)
        else:
            self._set_poster(PLACEHOLDER)
        if (config.plugins.ciefpepginfo.translate_epg.value
                and config.plugins.ciefpepginfo.translate_epg_description.value
                and config.plugins.ciefpepginfo.groq_api_key.value.strip()):
            target = config.plugins.ciefpepginfo.translate_to.value
            threading.Thread(
                target=self._translate_description_async,
                args=(description, target),
                daemon=True
            ).start()

    def _update_ui_with_tmdb(self, details, media_type):
        title = details.get("title") if media_type == "movie" else details.get("name", "")
        year = (details.get("release_date") or "")[:4] if media_type == "movie" else \
               (details.get("first_air_date") or "")[:4]

        self["title"].setText(title + (f" ({year})" if year else ""))

        if media_type == "movie":
            runtime = details.get("runtime")
            dur_text = f"Duration: {runtime} min" if runtime else self["duration"].text
        else:
            ert = details.get("episode_run_time")
            if ert and isinstance(ert, list) and ert:
                dur_text = f"Duration: ~{ert[0]} min/ep"
            else:
                dur_text = self["duration"].text
        self["duration"].setText(dur_text)

        vote = details.get("vote_average", 0)
        self["rating"].setText(f"TMDB: {vote:.1f}/10 ★" if vote else "TMDB: N/A")

        if config.plugins.ciefpepginfo.show_imdb_rating.value and config.plugins.ciefpepginfo.omdb_api_key.value:
            self["imdb_rating"].setText("IMDB: Loading...")
            threading.Thread(
                target=self._fetch_imdb_async,
                args=(details, media_type),
                daemon=True
            ).start()
        else:
            self["imdb_rating"].setText("")

        genres = [g["name"] for g in details.get("genres", [])]
        self["genres"].setText("Genres: " + (", ".join(genres) if genres else "N/A"))

        credits = details.get("credits", {})
        crew = credits.get("crew", [])
        directors = [c["name"] for c in crew if c.get("job") == "Director"]
        if media_type == "tv":
            creators = [c["name"] for c in details.get("created_by", [])]
            if creators:
                self["director"].setText("Created by: " + ", ".join(creators[:3]))
            elif directors:
                self["director"].setText("Director: " + ", ".join(directors[:3]))
            else:
                self["director"].setText("")
        else:
            if directors:
                self["director"].setText("Director: " + ", ".join(directors[:3]))
            else:
                self["director"].setText("")

        overview = (details.get("overview") or "").strip()
        if overview:
            if len(overview) > 750:
                cut = overview[:750].rfind(". ")
                if cut > 400:
                    overview = overview[:cut + 1] + " ..."
                else:
                    overview = overview[:750] + " ..."
            self["plot"].setText("Plot:\n" + overview)
            if (config.plugins.ciefpepginfo.translate_epg.value
                    and config.plugins.ciefpepginfo.translate_tmdb_overview.value
                    and config.plugins.ciefpepginfo.groq_api_key.value.strip()):
                target = config.plugins.ciefpepginfo.translate_to.value
                threading.Thread(
                    target=self._translate_tmdb_overview_async,
                    args=(overview, target),
                    daemon=True
                ).start()

        cast = credits.get("cast", [])[:10]
        if cast:
            self["cast_header"].setText("Cast:")
            first_row = cast[:5]
            second_row = cast[5:10]

            def format_actor(actor):
                name = actor.get("name", "").strip()
                char = actor.get("character", "").strip()
                if len(char) > 30:
                    char = char[:30] + "…"
                if char:
                    return f"• {name} as {char}"
                return f"• {name}"

            col1_text = "\n".join([format_actor(a) for a in first_row]) if first_row else ""
            self["cast_col1"].setText(col1_text)
            col2_text = "\n".join([format_actor(a) for a in second_row]) if second_row else ""
            self["cast_col2"].setText(col2_text)
        else:
            self["cast_header"].setText("")
            self["cast_col1"].setText("")
            self["cast_col2"].setText("")

        # ← IZMENA: trajler fetch uklonjen

        poster_path = details.get("poster_path")
        media_id = details.get("id")
        if poster_path and media_id:
            self._download_poster_async(poster_path, media_id, media_type)
        else:
            genres_list = [g["name"] for g in details.get("genres", [])]
            placeholder = choose_placeholder(genres_list)
            if placeholder == PLACEHOLDER:
                if media_type == "movie":
                    placeholder = PLACEHOLDER_MOVIE if os.path.exists(PLACEHOLDER_MOVIE) else PLACEHOLDER
                elif media_type == "tv":
                    placeholder = PLACEHOLDER_SERIES if os.path.exists(PLACEHOLDER_SERIES) else PLACEHOLDER
            self._set_poster(placeholder)

    def _fetch_imdb_async(self, details, media_type):
        try:
            rating = _omdb_rating(details, media_type,
                                  config.plugins.ciefpepginfo.omdb_api_key.value)
            if rating:
                self["imdb_rating"].setText(f"IMDB: {rating}/10 ★")
            else:
                self["imdb_rating"].setText("IMDB: N/A")
        except Exception:
            self["imdb_rating"].setText("IMDB: N/A")

    # ← IZMENA: _fetch_trailer_async je UKLONJEN

    # ---------- POSTER ----------
    def _download_poster_async(self, poster_path, media_id, media_type):
        if not poster_path or not media_id:
            self._set_poster(PLACEHOLDER)
            return
        if not config.plugins.ciefpepginfo.cache_enabled.value:
            self._set_poster(PLACEHOLDER)
            return

        def worker():
            try:
                folder = ensure_cache_folder()
                fname = os.path.join(
                    folder,
                    f"poster_{media_type}_{media_id}_{os.path.basename(poster_path)}"
                )
                if not os.path.exists(fname):
                    url = "https://image.tmdb.org/t/p/w500" + poster_path
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    data = urllib.request.urlopen(url, context=ctx, timeout=12).read()
                    with open(fname, "wb") as f:
                        f.write(data)
                self._set_poster(fname)
            except Exception as e:
                print("[CiefpEPGinfo] poster download error:", e)
                self._set_poster(PLACEHOLDER)

        threading.Thread(target=worker, daemon=True).start()

    def _set_poster(self, path):
        px = load_pixmap_safe(path)
        if px and self["poster"].instance:
            try:
                self["poster"].instance.setPixmap(px)
                self["poster"].show()
                return
            except Exception:
                pass
        px = load_pixmap_safe(PLACEHOLDER)
        if px and self["poster"].instance:
            try:
                self["poster"].instance.setPixmap(px)
                self["poster"].show()
            except Exception:
                pass

    # ---------- ACTIONS ----------
    def on_ok(self):
        # ← U bouquet modu OK pokreće kanal
        if self.bouquet_mode:
            idx = self["epg_list"].getSelectedIndex()
            if not (0 <= idx < len(self.bouquet_channels)):
                return
            display_name = self.bouquet_channels[idx]
            raw_ref = self.bouquet_channel_refs.get(display_name, "")

            # Marker – ne radi ništa
            if not raw_ref or "1:64:" in raw_ref or display_name.startswith("["):
                self["status"].setText(f"Marker: {display_name}  (nije kanal)")
                return

            ref = raw_ref_to_eServiceReference(raw_ref)
            if ref is None:
                try:
                    ref_str = raw_ref.strip()
                    if ref_str.startswith("#SERVICE"):
                        ref_str = ref_str[9:].strip()
                    ref = eServiceReference(ref_str)
                    if not ref.valid():
                        self["status"].setText("Cannot play this stream")
                        return
                except Exception as e:
                    print(f"[CiefpEPGinfo] IPTV play error: {e}")
                    self["status"].setText("Play error")
                    return

            self["status"].setText(f"Playing: {display_name}...")
            try:
                self.session.nav.playService(ref)
            except Exception as e:
                print(f"[CiefpEPGinfo] playService error: {e}")
                self["status"].setText("Play error")
            return

        # Normalni mod – TMDB detalji
        idx = self["epg_list"].getSelectedIndex()
        if 0 <= idx < len(self.epg_events):
            self.current_event = self.epg_events[idx]
            self._process_event(self.current_event, is_current=(idx == 0))

    def on_up(self):
        try:
            self["epg_list"].up()
            if self.bouquet_mode:
                self._on_bouquet_channel_changed(self["epg_list"].getSelectedIndex())
        except Exception:
            pass

    def on_down(self):
        try:
            self["epg_list"].down()
            if self.bouquet_mode:
                self._on_bouquet_channel_changed(self["epg_list"].getSelectedIndex())
        except Exception:
            pass

    # ← IZMENA: show_trailer / _play_youtube su UKLONJENI

    def _translate_description_async(self, text, target):
        try:
            translated = _translate_cached(text, target)
            self["plot"].setText("Plot:\n" + translated)
            self["status"].setText(f"Translated to {target} ✓")
        except Exception as e:
            print("[CiefpEPGinfo] translate description error:", e)

    def _translate_tmdb_overview_async(self, text, target):
        try:
            translated = _translate_cached(text, target)
            self["plot"].setText("Plot:\n" + translated)
            self["status"].setText(f"Plot translated to {target} ✓")
        except Exception as e:
            print("[CiefpEPGinfo] translate tmdb overview error:", e)

    def _translate_biography_async(self, text, target):
        try:
            translated = _translate_cached(text, target)
            self["plot"].setText("Biography:\n" + translated)
            self["status"].setText(f"Biography translated to {target} ✓")
        except Exception as e:
            print("[CiefpEPGinfo] translate biography error:", e)

    # ---------- Filmography ----------
    def filmography_browser(self):
        if hasattr(self, 'current_person_details') and self.current_person_details:
            self._show_person_filmography_choicebox()
            return
        if not self.current_media_details:
            self["status"].setText("No TMDB info loaded")
            return
        credits = self.current_media_details.get("credits", {})
        cast = credits.get("cast", [])
        crew = credits.get("crew", [])
        directors = [c for c in crew if c.get("job") == "Director"]
        menu = []
        if directors:
            for d in directors[:3]:
                menu.append((f"🎬 Director: {d.get('name', '')}", d))
        for i, a in enumerate(cast[:25]):
            name = a.get("name", "")
            char = a.get("character", "")
            if len(char) > 30:
                char = char[:30] + "…"
            if char:
                menu.append((f"{i + 1}. {name} ({char})", a))
            else:
                menu.append((f"{i + 1}. {name}", a))
        if not menu:
            self["status"].setText("No cast info")
            return

        def person_selected(choice):
            if not choice:
                return
            person = choice[1]
            name = person.get("name", "")
            if not name:
                return
            self["status"].setText(f"Loading filmography: {name}...")
            threading.Thread(
                target=self._load_person_for_filmography,
                args=(name,),
                daemon=True
            ).start()

        title = self.current_media_details.get("title") or \
                self.current_media_details.get("name", "")
        self.session.openWithCallback(
            person_selected, ChoiceBox,
            title=f"Filmography Browser: {title}",
            list=menu
        )

    def _load_person_for_filmography(self, name):
        api_key = config.plugins.ciefpepginfo.tmdb_api_key.value.strip()
        if not api_key:
            self["status"].setText("TMDB API key not set")
            return
        result = _tmdb_search_person(name, api_key)
        if not result:
            self["status"].setText(f"Person not found: {name}")
            return
        person_id = result.get("id")
        details = _tmdb_person_details(person_id, api_key)
        if not details:
            self["status"].setText(f"Person details error: {name}")
            return
        self.current_person_details = details
        self.current_person_name = details.get("name", name)
        self._show_person_filmography_choicebox()

    def _show_person_filmography_choicebox(self):
        if not self.current_person_details:
            self["status"].setText("No person loaded")
            return
        person = self.current_person_details
        person_name = person.get("name", "Unknown")
        movie_credits = person.get("movie_credits", {}).get("cast", [])
        tv_credits = person.get("tv_credits", {}).get("cast", [])
        seen_m = set()
        unique_movies = []
        for m in movie_credits:
            if m.get("id") not in seen_m:
                seen_m.add(m.get("id"))
                unique_movies.append(m)
        seen_t = set()
        unique_tv = []
        for t in tv_credits:
            if t.get("id") not in seen_t:
                seen_t.add(t.get("id"))
                unique_tv.append(t)

        def score(x):
            pop = x.get("popularity", 0) or 0
            votes = x.get("vote_count", 0) or 0
            return votes * 10 + pop

        unique_movies.sort(key=score, reverse=True)
        unique_tv.sort(key=score, reverse=True)
        top_movies = unique_movies[:10]
        top_tv = unique_tv[:10]

        menu = []
        if top_movies:
            menu.append((f"── MOVIES ({len(top_movies)}) ──", None))
            for m in top_movies:
                title = m.get("title", "N/A")
                year = (m.get("release_date") or "")[:4]
                rating = m.get("vote_average", 0) or 0
                year_str = f" ({year})" if year else ""
                rating_str = f" ★{rating:.1f}" if rating > 0 else ""
                menu.append((f"🎬 {title}{year_str}{rating_str}", ("movie", m)))
        if top_tv:
            menu.append((f"── TV SERIES ({len(top_tv)}) ──", None))
            for t in top_tv:
                name = t.get("name", "N/A")
                year = (t.get("first_air_date") or "")[:4]
                rating = t.get("vote_average", 0) or 0
                year_str = f" ({year})" if year else ""
                rating_str = f" ★{rating:.1f}" if rating > 0 else ""
                menu.append((f"📺 {name}{year_str}{rating_str}", ("tv", t)))
        if not menu:
            self["status"].setText(f"No filmography for {person_name}")
            return

        def media_selected(choice):
            if not choice or choice[1] is None:
                return
            media_type, media_data = choice[1]
            media_id = media_data.get("id")
            title = media_data.get("title") or media_data.get("name", "Unknown")
            if media_id:
                self["status"].setText(f"Loading {title}...")
                threading.Thread(
                    target=self._load_media_from_filmography,
                    args=(media_id, media_type, title),
                    daemon=True
                ).start()

        self.session.openWithCallback(
            media_selected, ChoiceBox,
            title=f"Filmography: {person_name}",
            list=menu
        )

    def _load_media_from_filmography(self, media_id, media_type, media_title):
        api_key = config.plugins.ciefpepginfo.tmdb_api_key.value.strip()
        if not api_key:
            self["status"].setText("TMDB API key not set")
            return
        try:
            details = _tmdb_details(media_id, media_type, api_key)
            if not details:
                self["status"].setText("Error loading media details")
                return
            if not self._saved_media_state:
                self._saved_media_state = {
                    "media_details": self.current_media_details,
                    "media_type": self.current_media_type,
                }
            self.current_media_details = details
            self.current_media_type = media_type
            self._update_ui_with_tmdb(details, media_type)
            person_name = getattr(self, 'current_person_name', '')
            if person_name:
                self["epg_title"].setText(f"From filmography: {person_name}")
            self["status"].setText(f"Loaded: {media_title} ✓")
        except Exception as e:
            print("[CiefpEPGinfo] load media from filmography error:", e)
            self["status"].setText("Error loading media")

    def cast_explore(self):
        if not self.current_media_details:
            self["status"].setText("No TMDB info loaded")
            return
        credits = self.current_media_details.get("credits", {})
        cast = credits.get("cast", [])
        crew = credits.get("crew", [])
        directors = [c for c in crew if c.get("job") == "Director"]
        menu = []
        if directors:
            for d in directors[:2]:
                menu.append((f"🎬 Director: {d.get('name', '')}", d))
        for i, a in enumerate(cast[:20]):
            name = a.get("name", "")
            char = a.get("character", "")
            if len(char) > 30:
                char = char[:30] + "…"
            menu.append((f"{i + 1}. {name} ({char})", a))
        if not menu:
            self["status"].setText("No cast info")
            return

        def cb(choice):
            if choice:
                person = choice[1]
                name = person.get("name", "")
                if name:
                    self["status"].setText(f"Loading: {name}...")
                    threading.Thread(
                        target=self._load_person_async,
                        args=(name,),
                        daemon=True
                    ).start()

        title = self.current_media_details.get("title") or \
                self.current_media_details.get("name", "")
        self.session.openWithCallback(cb, ChoiceBox,
                                      title=f"Cast & Crew: {title}",
                                      list=menu)

    def _load_person_async(self, name):
        api_key = config.plugins.ciefpepginfo.tmdb_api_key.value.strip()
        if not api_key:
            self["status"].setText("TMDB API key not set")
            return
        result = _tmdb_search_person(name, api_key)
        if not result:
            self["status"].setText(f"Person not found: {name}")
            return
        person_id = result.get("id")
        details = _tmdb_person_details(person_id, api_key)
        if not details:
            self["status"].setText(f"Person details error: {name}")
            return
        self._saved_media_state = {
            "media_details": self.current_media_details,
            "media_type": self.current_media_type,
        }
        self._display_person_info(details)

    def _display_person_info(self, details):
        person_id = details.get("id")
        name = details.get("name", "N/A")
        known_for = details.get("known_for_department", "")
        birthday = details.get("birthday", "")
        deathday = details.get("deathday", "")
        place_of_birth = details.get("place_of_birth", "")
        biography = details.get("biography", "").strip()

        movie_credits = details.get("movie_credits", {}).get("cast", [])
        tv_credits = details.get("tv_credits", {}).get("cast", [])
        movie_ids = set()
        unique_movies = []
        for m in movie_credits:
            if m.get("id") not in movie_ids:
                movie_ids.add(m.get("id"))
                unique_movies.append(m)
        tv_ids = set()
        unique_tv = []
        for t in tv_credits:
            if t.get("id") not in tv_ids:
                tv_ids.add(t.get("id"))
                unique_tv.append(t)
        movie_count = len(unique_movies)
        tv_count = len(unique_tv)

        self["title"].setText(name + (f"  ({known_for})" if known_for else ""))
        self["epg_title"].setText("Actor Profile")

        if birthday:
            try:
                y, m, d = birthday.split("-")
                pretty_birth = f"{int(d):02d}.{int(m):02d}.{y}"
            except Exception:
                pretty_birth = birthday
        else:
            pretty_birth = "N/A"

        self["duration"].setText(f"Born: {pretty_birth}")
        self["rating"].setText(f"Place: {place_of_birth}" if place_of_birth else "")
        self["imdb_rating"].setText(f"Movies: {movie_count}  |  TV Series: {tv_count}")
        self["director"].setText("")

        if deathday:
            try:
                y, m, d = deathday.split("-")
                pretty_death = f"{int(d):02d}.{int(m):02d}.{y}"
            except Exception:
                pretty_death = deathday
            self["genres"].setText(f"Died: {pretty_death}")
        else:
            self["genres"].setText("")

        if biography:
            biography = re.sub(r"\n{2,}", "\n", biography).strip()
            MAX_BIO = 700
            if len(biography) > MAX_BIO:
                cut = biography[:MAX_BIO].rfind(". ")
                if cut > 400:
                    biography = biography[:cut + 1] + " ..."
                else:
                    cut = biography[:MAX_BIO].rfind(" ")
                    if cut > 400:
                        biography = biography[:cut] + " ..."
                    else:
                        biography = biography[:MAX_BIO] + " ..."
            self["plot"].setText("Biography:\n" + biography)
            if (config.plugins.ciefpepginfo.translate_epg.value
                    and config.plugins.ciefpepginfo.translate_biography.value
                    and config.plugins.ciefpepginfo.groq_api_key.value.strip()):
                target = config.plugins.ciefpepginfo.translate_to.value
                threading.Thread(
                    target=self._translate_biography_async,
                    args=(biography, target),
                    daemon=True
                ).start()

        self["cast_header"].setText("Known For:")

        def movie_score(m):
            pop = m.get("popularity", 0) or 0
            votes = m.get("vote_count", 0) or 0
            return votes * 10 + pop

        def tv_score(t):
            pop = t.get("popularity", 0) or 0
            votes = t.get("vote_count", 0) or 0
            return votes * 10 + pop

        unique_movies.sort(key=movie_score, reverse=True)
        unique_tv.sort(key=tv_score, reverse=True)
        top_movies = unique_movies[:5]
        top_tv = unique_tv[:5]

        def fmt_movie(m):
            title = m.get("title", "N/A")
            year = (m.get("release_date") or "")[:4]
            rating = m.get("vote_average", 0) or 0
            year_str = f" ({year})" if year else ""
            rating_str = f" {rating:.1f}★" if rating > 0 else ""
            return f"• {title}{year_str}{rating_str}"

        def fmt_tv(t):
            name = t.get("name", "N/A")
            year = (t.get("first_air_date") or "")[:4]
            rating = t.get("vote_average", 0) or 0
            year_str = f" ({year})" if year else ""
            rating_str = f" {rating:.1f}★" if rating > 0 else ""
            return f"• {name}{year_str}{rating_str}"

        col1_text = "\n".join([fmt_movie(m) for m in top_movies]) if top_movies else "No movies"
        col2_text = "\n".join([fmt_tv(t) for t in top_tv]) if top_tv else "No TV series"
        col1_text = "Movies:\n" + col1_text
        col2_text = "TV Series:\n" + col2_text
        self["cast_col1"].setText(col1_text)
        self["cast_col2"].setText(col2_text)

        profile_path = details.get("profile_path")
        if profile_path:
            self._download_person_photo_async(profile_path, person_id)
        else:
            self._set_poster(PLACEHOLDER)

        self["status"].setText(f"Profile: {name}  (BACK to return)")

    def _download_person_photo_async(self, profile_path, person_id):
        if not profile_path or not person_id:
            self._set_poster(PLACEHOLDER)
            return
        if not config.plugins.ciefpepginfo.cache_enabled.value:
            self._set_poster(PLACEHOLDER)
            return

        def worker():
            try:
                folder = ensure_cache_folder()
                fname = os.path.join(
                    folder,
                    f"person_{person_id}_{os.path.basename(profile_path)}"
                )
                if not os.path.exists(fname):
                    url = "https://image.tmdb.org/t/p/w500" + profile_path
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    data = urllib.request.urlopen(url, context=ctx, timeout=12).read()
                    with open(fname, "wb") as f:
                        f.write(data)
                self._set_poster(fname)
            except Exception as e:
                print("[CiefpEPGinfo] person photo error:", e)
                self._set_poster(PLACEHOLDER)

        threading.Thread(target=worker, daemon=True).start()

    def open_settings(self):
        self.session.open(SettingsScreen)

    def keyBack(self):
        """BACK – prvo izađi iz bouquet moda, pa iz profila, pa zatvori"""
        # 1) Ako smo u bouquet modu – vrati se na normalni EPG
        if self.bouquet_mode:
            self._exit_bouquet_mode()
            return
        # 2) Ako smo na profilu osobe – vrati se na film
        if self._saved_media_state and self._saved_media_state.get("media_details"):
            self.current_media_details = self._saved_media_state["media_details"]
            self.current_media_type = self._saved_media_state["media_type"]
            self._saved_media_state = None
            self._update_ui_with_tmdb(self.current_media_details, self.current_media_type)
            self["status"].setText("Returned to movie")
            return
        # 3) Inače zatvori ekran
        self.close()


# ---------- SETTINGS SCREEN ----------
class SettingsScreen(Screen):
    skin = """
        <screen name="CiefpEPGinfoSettings" position="center,center" size="1700,800"
                title="..:: CiefpEPGinfo Settings ::.." backgroundColor="#011a2e">
            <widget name="menu" position="50,50" size="1000,600" scrollbarMode="showOnDemand"
                    itemHeight="50" font="Regular;28" backgroundColor="#011a2e"/>
            <widget name="background" position="1100,0" size="500,750" pixmap="%s" alphatest="on" />        
            <widget name="status" position="50,670" size="1300,40" font="Regular;26"
                    foregroundColor="#00FF00" backgroundColor="#011a2e"/>
            <ePixmap pixmap="buttons/red.png" position="0,740" size="35,35" alphatest="blend"/>
            <eLabel text="Cancel" position="50,730" size="200,50" font="Regular;28"
                    foregroundColor="white" backgroundColor="#800000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/green.png" position="260,740" size="35,35" alphatest="blend"/>
            <eLabel text="Save" position="310,730" size="200,50" font="Regular;28"
                    foregroundColor="white" backgroundColor="#008000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/yellow.png" position="520,740" size="35,35" alphatest="blend"/>
            <eLabel text="TMDB Key" position="570,730" size="200,50" font="Regular;28"
                    foregroundColor="white" backgroundColor="#808000" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/blue.png" position="780,740" size="35,35" alphatest="blend"/>
            <eLabel text="OMDB Key" position="830,730" size="200,50" font="Regular;28"
                    foregroundColor="white" backgroundColor="#000080" halign="center" valign="center"/>
            <ePixmap pixmap="buttons/red.png" position="1040,740" size="35,35" alphatest="blend"/>
            <eLabel text="GROQ Key" position="1090,730" size="200,50" font="Regular;28"
                    foregroundColor="white" backgroundColor="#400080" halign="center" valign="center"/>
        </screen>
    """% BACKGROUND_SETTINGS

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self["menu"] = MenuList([])
        self["status"] = Label("Settings")
        self["background"] = Pixmap()
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "cancel": self.close,
                "red": self.close,
                "green": self.save_all,
                "yellow": self.edit_tmdb,
                "blue": self.edit_omdb,
                "menu": self.edit_groq,
                "ok": self.on_ok,
            }, -1)
        self.onLayoutFinish.append(self.build_menu)

    def build_menu(self):
        tmdb = "✓ SET" if config.plugins.ciefpepginfo.tmdb_api_key.value else "✗ NOT SET"
        omdb = "✓ SET" if config.plugins.ciefpepginfo.omdb_api_key.value else "✗ NOT SET"
        groq = "✓ SET" if config.plugins.ciefpepginfo.groq_api_key.value else "✗ NOT SET"
        cache = config.plugins.ciefpepginfo.cache_folder.value
        cache_on = "YES" if config.plugins.ciefpepginfo.cache_enabled.value else "NO"
        imdb_on = "YES" if config.plugins.ciefpepginfo.show_imdb_rating.value else "NO"
        trans_on = "YES" if config.plugins.ciefpepginfo.translate_epg.value else "NO"
        lang_code = config.plugins.ciefpepginfo.language.value
        lang_map = {
            "en-US": "English", "sr-RS": "Srpski", "hr-HR": "Hrvatski",
            "bs-BA": "Bosanski", "sl-SI": "Slovenščina", "mk-MK": "Македонски",
            "cs-CZ": "Čeština", "sk-SK": "Slovenský", "hu-HU": "Magyar",
            "ro-RO": "Română", "bg-BG": "Български", "el-GR": "Ελληνικά",
            "de-DE": "Deutsch", "fr-FR": "Français", "es-ES": "Español",
            "it-IT": "Italiano", "pt-PT": "Português PT", "pt-BR": "Português BR",
            "nl-NL": "Nederlands", "sv-SE": "Svenska", "no-NO": "Norsk",
            "da-DK": "Dansk", "fi-FI": "Suomi", "ru-RU": "Русский",
            "uk-UA": "Українська", "pl-PL": "Polski", "tr-TR": "Türkçe",
            "ar-AE": "العربية", "he-IL": "עברית", "ja-JP": "日本語",
            "ko-KR": "한국어", "zh-CN": "中文 (简)", "zh-TW": "中文 (繁)",
            "th-TH": "ไทย", "vi-VN": "Tiếng Việt",
        }
        lang = lang_map.get(lang_code, lang_code)

        cache_count, cache_size = get_cache_info()
        cache_info = f"{cache_count} files ({cache_size:.1f} MB)"

        tlang_code = config.plugins.ciefpepginfo.translate_to.value
        tlang_map = {
            "sr": "Srpski", "hr": "Hrvatski", "bs": "Bosanski",
            "sl": "Slovenščina", "mk": "Македонски", "en": "English",
            "de": "Deutsch", "fr": "Français", "es": "Español",
            "it": "Italiano", "ru": "Русский", "pt": "Português",
            "pl": "Polski", "cs": "Čeština", "hu": "Magyar",
            "ro": "Română", "bg": "Български", "el": "Ελληνικά",
            "tr": "Türkçe", "nl": "Nederlands", "sv": "Svenska",
            "ar": "العربية",
        }
        tlang = tlang_map.get(tlang_code, tlang_code)

        epg_desc_on = "YES" if config.plugins.ciefpepginfo.translate_epg_description.value else "NO"
        tmdb_ov_on = "YES" if config.plugins.ciefpepginfo.translate_tmdb_overview.value else "NO"
        bio_on = "YES" if config.plugins.ciefpepginfo.translate_biography.value else "NO"
        titles_on = "YES" if config.plugins.ciefpepginfo.translate_titles.value else "NO"
        groq_model_code = config.plugins.ciefpepginfo.groq_model.value
        groq_model_map = {
            "openai/gpt-oss-120b": "GPT-OSS 120B",
            "openai/gpt-oss-20b": "GPT-OSS 20B",
            "llama-3.3-70b-versatile": "Llama 3.3 70B",
            "llama-3.1-8b-instant": "Llama 3.1 8B",
            "meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout 17B",
            "meta-llama/llama-4-maverick-17b-128e-instruct": "Llama 4 Maverick 17B",
            "qwen/qwen3-32b": "Qwen3 32B",
            "moonshotai/kimi-k2-instruct": "Kimi K2",
            "deepseek-r1-distill-llama-70b": "DeepSeek R1 70B",
        }
        groq_model = groq_model_map.get(groq_model_code, groq_model_code)

        items = [
            f"TMDB API Key:         {tmdb}",
            f"OMDb API Key:         {omdb}",
            f"GROQ API Key:         {groq}",
            f"GROQ Model:           {groq_model}",
            f"Cache folder:         {cache}",
            f"Download Posters:     {cache_on}",
            f"Show IMDB Rating:     {imdb_on}",
            f"Description lang:     {lang}",
            "─────────────────────────────────",
            f"GROQ Translate:       {trans_on}",
            f"Translate to:         {tlang}",
            f"  → EPG description:  {epg_desc_on}",
            f"  → TMDB Plot:        {tmdb_ov_on}",
            f"  → Biography:        {bio_on}",
            f"  → Titles:           {titles_on}",
            "─────────────────────────────────",
            f"Cache size:           {cache_info}",
            ">>> CLEAR CACHE (press OK) <<<",
            "─────────────────────────────────",
            ">>> Manual Update (MENU) <<<",
        ]
        self["menu"].setList(items)

    def on_ok(self):
        idx = self["menu"].getSelectedIndex()
        if idx == 0:
            self.edit_tmdb()
        elif idx == 1:
            self.edit_omdb()
        elif idx == 2:
            self.edit_groq()
        elif idx == 3:
            self._cycle_groq_model()
        elif idx == 5:
            config.plugins.ciefpepginfo.cache_enabled.value = \
                not config.plugins.ciefpepginfo.cache_enabled.value
            self.build_menu()
        elif idx == 6:
            config.plugins.ciefpepginfo.show_imdb_rating.value = \
                not config.plugins.ciefpepginfo.show_imdb_rating.value
            self.build_menu()
        elif idx == 7:
            self._cycle_language()
        elif idx == 9:
            config.plugins.ciefpepginfo.translate_epg.value = \
                not config.plugins.ciefpepginfo.translate_epg.value
            self.build_menu()
        elif idx == 10:
            self._cycle_translate_language()
        elif idx == 11:
            config.plugins.ciefpepginfo.translate_epg_description.value = \
                not config.plugins.ciefpepginfo.translate_epg_description.value
            self.build_menu()
        elif idx == 12:
            config.plugins.ciefpepginfo.translate_tmdb_overview.value = \
                not config.plugins.ciefpepginfo.translate_tmdb_overview.value
            self.build_menu()
        elif idx == 13:
            config.plugins.ciefpepginfo.translate_biography.value = \
                not config.plugins.ciefpepginfo.translate_biography.value
            self.build_menu()
        elif idx == 14:
            config.plugins.ciefpepginfo.translate_titles.value = \
                not config.plugins.ciefpepginfo.translate_titles.value
            self.build_menu()
        elif idx == 17:
            self.clear_cache_dialog()
        elif idx == 19:
            self.manual_update_dialog()

    def _cycle_language(self):
        lang_order = [
            "en-US", "sr-RS", "hr-HR", "bs-BA", "sl-SI", "mk-MK",
            "cs-CZ", "sk-SK", "hu-HU", "ro-RO", "bg-BG", "el-GR",
            "de-DE", "fr-FR", "es-ES", "it-IT", "pt-PT", "pt-BR",
            "nl-NL", "sv-SE", "no-NO", "da-DK", "fi-FI", "ru-RU",
            "uk-UA", "pl-PL", "tr-TR", "ar-AE", "he-IL", "ja-JP",
            "ko-KR", "zh-CN", "zh-TW", "th-TH", "vi-VN",
        ]
        lang_names = {
            "en-US": "English", "sr-RS": "Srpski", "hr-HR": "Hrvatski",
            "bs-BA": "Bosanski", "sl-SI": "Slovenščina", "mk-MK": "Македонски",
            "cs-CZ": "Čeština", "sk-SK": "Slovenský", "hu-HU": "Magyar",
            "ro-RO": "Română", "bg-BG": "Български", "el-GR": "Ελληνικά",
            "de-DE": "Deutsch", "fr-FR": "Français", "es-ES": "Español",
            "it-IT": "Italiano", "pt-PT": "Português PT", "pt-BR": "Português BR",
            "nl-NL": "Nederlands", "sv-SE": "Svenska", "no-NO": "Norsk",
            "da-DK": "Dansk", "fi-FI": "Suomi", "ru-RU": "Русский",
            "uk-UA": "Українська", "pl-PL": "Polski", "tr-TR": "Türkçe",
            "ar-AE": "العربية", "he-IL": "עברית", "ja-JP": "日本語",
            "ko-KR": "한국어", "zh-CN": "中文 (简)", "zh-TW": "中文 (繁)",
            "th-TH": "ไทย", "vi-VN": "Tiếng Việt",
        }
        cur = config.plugins.ciefpepginfo.language.value
        try:
            i = lang_order.index(cur)
        except ValueError:
            i = 0
        nxt = lang_order[(i + 1) % len(lang_order)]
        config.plugins.ciefpepginfo.language.value = nxt
        config.plugins.ciefpepginfo.language.save()
        configfile.save()
        self["status"].setText(f"Language → {lang_names.get(nxt, nxt)}")
        self.build_menu()

    def _cycle_translate_language(self):
        lang_order = [
            "sr", "hr", "bs", "sl", "mk", "en",
            "de", "fr", "es", "it", "ru", "pt",
            "pl", "cs", "hu", "ro", "bg", "el",
            "tr", "nl", "sv", "ar",
        ]
        lang_names = {
            "sr": "Srpski", "hr": "Hrvatski", "bs": "Bosanski",
            "sl": "Slovenščina", "mk": "Македонски", "en": "English",
            "de": "Deutsch", "fr": "Français", "es": "Español",
            "it": "Italiano", "ru": "Русский", "pt": "Português",
            "pl": "Polski", "cs": "Čeština", "hu": "Magyar",
            "ro": "Română", "bg": "Български", "el": "Ελληνικά",
            "tr": "Türkçe", "nl": "Nederlands", "sv": "Svenska",
            "ar": "العربية",
        }
        cur = config.plugins.ciefpepginfo.translate_to.value
        try:
            i = lang_order.index(cur)
        except ValueError:
            i = 0
        nxt = lang_order[(i + 1) % len(lang_order)]
        config.plugins.ciefpepginfo.translate_to.value = nxt
        config.plugins.ciefpepginfo.translate_to.save()
        configfile.save()
        self["status"].setText(f"Translate to → {lang_names.get(nxt, nxt)}")
        self.build_menu()

    def _cycle_groq_model(self):
        model_order = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "qwen/qwen3-32b",
            "moonshotai/kimi-k2-instruct",
            "deepseek-r1-distill-llama-70b",
        ]
        model_names = {
            "openai/gpt-oss-120b": "GPT-OSS 120B",
            "openai/gpt-oss-20b": "GPT-OSS 20B",
            "llama-3.3-70b-versatile": "Llama 3.3 70B",
            "llama-3.1-8b-instant": "Llama 3.1 8B",
            "meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout 17B",
            "meta-llama/llama-4-maverick-17b-128e-instruct": "Llama 4 Maverick 17B",
            "qwen/qwen3-32b": "Qwen3 32B",
            "moonshotai/kimi-k2-instruct": "Kimi K2",
            "deepseek-r1-distill-llama-70b": "DeepSeek R1 70B",
        }
        cur = config.plugins.ciefpepginfo.groq_model.value
        try:
            i = model_order.index(cur)
        except ValueError:
            i = 0
        nxt = model_order[(i + 1) % len(model_order)]
        config.plugins.ciefpepginfo.groq_model.value = nxt
        config.plugins.ciefpepginfo.groq_model.save()
        configfile.save()
        self["status"].setText(f"GROQ Model → {model_names.get(nxt, nxt)}")
        self.build_menu()

    def edit_tmdb(self):
        def cb(res):
            if res is not None:
                config.plugins.ciefpepginfo.tmdb_api_key.value = res.strip()
                config.plugins.ciefpepginfo.tmdb_api_key.save()
                _save_key_to_file(TMDB_API_KEY_FILE, res)
                self["status"].setText("TMDB key saved")
                self.build_menu()
        self.session.openWithCallback(cb, VirtualKeyBoard,
                                      title="TMDB API Key",
                                      text=config.plugins.ciefpepginfo.tmdb_api_key.value)

    def edit_omdb(self):
        def cb(res):
            if res is not None:
                config.plugins.ciefpepginfo.omdb_api_key.value = res.strip()
                config.plugins.ciefpepginfo.omdb_api_key.save()
                _save_key_to_file(OMDB_API_KEY_FILE, res)
                self["status"].setText("OMDb key saved")
                self.build_menu()
        self.session.openWithCallback(cb, VirtualKeyBoard,
                                      title="OMDb API Key",
                                      text=config.plugins.ciefpepginfo.omdb_api_key.value)

    def edit_groq(self):
        def cb(res):
            if res is not None:
                config.plugins.ciefpepginfo.groq_api_key.value = res.strip()
                config.plugins.ciefpepginfo.groq_api_key.save()
                _save_key_to_file(GROQ_API_KEY_FILE, res)
                self["status"].setText("GROQ key saved")
                self.build_menu()
        self.session.openWithCallback(cb, VirtualKeyBoard,
                                      title="GROQ API Key",
                                      text=config.plugins.ciefpepginfo.groq_api_key.value)

    def clear_cache_dialog(self):
        count, size = get_cache_info()
        if count == 0:
            self["status"].setText("Cache is already empty!")
            return
        msg = (f"Delete {count} cached images ({size:.1f} MB)?\n\n"
               f"Folder: {config.plugins.ciefpepginfo.cache_folder.value}\n\n"
               f"This cannot be undone!")

        def confirm(result):
            if result:
                deleted, freed = clear_cache()
                self["status"].setText(f"Deleted {deleted} files ({freed:.1f} MB)")
                self.build_menu()
            else:
                self["status"].setText("Cancelled")

        self.session.openWithCallback(
            confirm, MessageBox, msg, MessageBox.TYPE_YESNO
        )

    def manual_update_dialog(self):
        msg = (f"Check for updates?\n\n"
               f"This will download the latest version\n"
               f"from GitHub and restart Enigma2.")

        def confirm(result):
            if result:
                self["status"].setText("Updating... please wait")
                os.system(UPDATE_COMMAND)

        self.session.openWithCallback(
            confirm, MessageBox, msg, MessageBox.TYPE_YESNO
        )

    def save_all(self):
        try:
            config.plugins.ciefpepginfo.tmdb_api_key.save()
            config.plugins.ciefpepginfo.omdb_api_key.save()
            config.plugins.ciefpepginfo.groq_api_key.save()
            config.plugins.ciefpepginfo.groq_model.save()
            config.plugins.ciefpepginfo.cache_enabled.save()
            config.plugins.ciefpepginfo.show_imdb_rating.save()
            config.plugins.ciefpepginfo.language.save()
            config.plugins.ciefpepginfo.translate_epg.save()
            config.plugins.ciefpepginfo.translate_to.save()
            config.plugins.ciefpepginfo.translate_epg_description.save()
            config.plugins.ciefpepginfo.translate_tmdb_overview.save()
            config.plugins.ciefpepginfo.translate_biography.save()
            config.plugins.ciefpepginfo.translate_titles.save()
            configfile.save()
            self["status"].setText("All settings saved!")
        except Exception as e:
            self["status"].setText(f"Error: {e}")

    def close(self):
        try:
            if "actions" in self:
                self["actions"].destroy()
                del self["actions"]
        except Exception:
            pass
        Screen.close(self)


# ---------- INIT ----------
load_all_api_keys()
ensure_cache_folder()


# ---------- PLUGIN ENTRY ----------
def main(session, **kwargs):
    session.open(CiefpEPGinfoMain)


def Plugins(**kwargs):
    icon = PLUGIN_ICON if os.path.exists(PLUGIN_ICON) else None
    return [
        PluginDescriptor(
            name=f"{PLUGIN_NAME} v{PLUGIN_VERSION}",
            description=PLUGIN_DESC,
            icon=icon,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main
        ),
        PluginDescriptor(
            name=f"{PLUGIN_NAME} v{PLUGIN_VERSION}",
            where=PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU,
            fnc=main
        ),
    ]