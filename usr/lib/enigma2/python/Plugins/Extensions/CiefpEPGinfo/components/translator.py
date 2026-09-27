# -*- coding: utf-8 -*-
# components/translator.py – za CiefpEPGinfo
from __future__ import absolute_import, print_function

import json
import os

try:
    import requests
except ImportError:
    requests = None

from Components.config import config


# Podržani jezici (kod -> ime za prompt)
LANGUAGE_NAMES = {
    "sr": "Serbian",
    "hr": "Croatian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "mk": "Macedonian",
    "sk": "Slovak",
    "es": "Spanish",
    "el": "Greek",
    "ar": "Arabic",
    "en": "English",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "ru": "Russian",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "pt": "Portuguese",
    "pl": "Polish",
    "cs": "Czech",
    "tr": "Turkish",
    "nl": "Dutch",
    "sv": "Swedish",
}


class Translator:
    """GROQ prevodilac za CiefpEPGinfo"""

    def __init__(self, api_key=None, model=None):
        # Uzmi iz config-a ako nije prosleđeno
        if api_key is None:
            try:
                api_key = config.plugins.ciefpepginfo.groq_api_key.value
            except Exception:
                api_key = ""
        if model is None:
            try:
                model = config.plugins.ciefpepginfo.groq_model.value
            except Exception:
                model = "openai/gpt-oss-120b"

        self.api_key = (api_key or "").strip()
        self.model = model or "openai/gpt-oss-120b"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_available(self):
        """Da li je prevodilac spreman za upotrebu"""
        return bool(self.api_key) and requests is not None

    def translate(self, text, target_language="sr", source_language=None):
        """
        Prevedi tekst preko GROQ API-ja.
        """
        if not text:
            return text
        if not self.api_key:
            print("[CiefpTranslator] API key not set")
            return text
        if requests is None:
            print("[CiefpTranslator] requests module not available")
            return text

        target_name = LANGUAGE_NAMES.get(target_language, "Serbian")

        # Inicijalizuj instruction
        instruction = ""

        # Specijalno za arapski – transliteracija
        if target_language == "ar":
            instruction = ("You are a professional translator. "
                           "Translate the following text into Arabic, "
                           "but write it using LATIN script (transliteration). "
                           "Example: write 'Marhaba' instead of 'مرحبا'. "
                           "Keep the same formatting, line breaks and structure. "
                           "Return ONLY the translation.")
        # Ako je zadat source_language
        elif source_language:
            source_name = LANGUAGE_NAMES.get(source_language, source_language)
            instruction = (f"You are a professional translator. "
                           f"Translate from {source_name} into {target_name}. "
                           f"Keep formatting and line breaks. "
                           f"Return ONLY the translation.")
        # Default
        else:
            instruction = (f"You are a professional translator. "
                           f"Translate the following text into {target_name}. "
                           f"Keep formatting and line breaks. "
                           f"Return ONLY the translation.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
            "max_tokens": 8000,
        }

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }

        try:
            r = requests.post(self.api_url, headers=headers,
                              json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[CiefpTranslator] GROQ HTTP {r.status_code}: {r.text[:300]}")
                return text
        except Exception as e:
            print("[CiefpTranslator] translate error:", e)
            return text

    def test_connection(self):
        """Test da li API ključ radi. Vraća (bool, str)"""
        if not self.api_key:
            return False, "API key not set"
        if requests is None:
            return False, "requests module not available"
        try:
            r = requests.post(
                self.api_url,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 8000,   # i za test – reasoning model!
                },
                timeout=15,
            )
            if r.status_code == 200:
                return True, "OK"
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return False, str(e)