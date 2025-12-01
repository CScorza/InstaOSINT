#!/usr/bin/env python3
# CScorza - OSINT Instagram (GUI + Email & Phone) - Full rewrite
# Versione Finale con GUI Scuro, Anteprima Immagine, Download e Ricerca Numero/Globale (Layout V15 - Stable)

import os
import sys
import subprocess
from pathlib import Path
from io import BytesIO
import urllib.parse
import json
import requests
import hmac
import hashlib
import uuid
from datetime import datetime
import re 
import csv 

# Moduli che richiedono installazione (Pillow, phonenumbers, pycountry, ttkthemes, requests)
# Definiamo le variabili come None per evitare NameError prima del tentativo di importazione/setup
tk = None
ttk = None
scrolledtext = None
messagebox = None
webbrowser = None
ThemedTk = None
Image = None
ImageTk = None
ImageDraw = None 
PhoneNumberType = None
filedialog = None

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    import webbrowser
    import phonenumbers
    from phonenumbers.phonenumberutil import region_code_for_country_code
    from phonenumbers import carrier, number_type, PhoneNumberType, is_possible_number, is_valid_number
    import pycountry
    from PIL import Image, ImageTk, ImageDraw 
    from ttkthemes import ThemedTk
except ImportError:
    # Se l'importazione fallisce, il setup_virtualenv dovrebbe intervenire
    pass 

# --- AGGIUNTA DIPENDENZE E SETUP VIRTUALENV (Invariato) ---

def setup_virtualenv():
    """Controlla e installa Tkinter, crea un virtualenv e installa le dipendenze."""
    script_path = Path(sys.argv[0]).resolve()
    script_dir = script_path.parent
    script_name = script_path.stem
    env_name = f"Virtualenv{script_name}"
    venv_path = script_dir / env_name
    requirements_file = script_dir / "requirements.txt"

    # ---------------------------
    # 0️⃣ Controllo Tkinter
    # ---------------------------
    try:
        import tkinter
        print("[✓] Tkinter disponibile.")
    except ModuleNotFoundError:
        print("⚠️ Tkinter non trovato. Tentativo di installazione python3-tk...")
        try:
            # Assumi ambiente Debian/Ubuntu per 'sudo apt install'
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "python3-tk"], check=True)
            print("[✓] Tkinter installato.\n")
        except Exception:
            print("⚠️ Installazione python3-tk fallita. Verifica la tua installazione manualmente.")

    # ---------------------------
    # 1️⃣ Controllo python3-venv
    # ---------------------------
    print("[+] Controllo pacchetto python3-venv...")
    try:
        pkg_installed = subprocess.run(
            ["dpkg", "-s", "python3-venv"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ).returncode == 0
    except FileNotFoundError:
        # dpkg non esiste (non-Debian/Ubuntu), assumiamo True
        pkg_installed = True 

    if not pkg_installed:
        print("⚠️ python3-venv non installato. Installazione in corso...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "python3-venv"], check=True)
        print("[✓] python3-venv installato.\n")
    else:
        print("[✓] python3-venv già installato.\n")
        
    # ---------------------------
    # 2️⃣ Creazione virtualenv
    # ---------------------------
    pip_path = venv_path / "bin" / "pip"
    python_venv = venv_path / "bin" / "python"

    if not venv_path.exists():
        print(f"[+] Creo virtualenv '{env_name}'...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("[✓] Virtualenv creato.\n")
    else:
        print(f"[!] Virtualenv '{env_name}' già esistente.\n")

    if not pip_path.exists():
        print("❌ pip non trovato nel virtualenv. ensurepip ancora mancante!")
        sys.exit(1)

    # ---------------------------
    # 3️⃣ Aggiunta e Installazione librerie
    # ---------------------------
    required_packages = ["requests", "phonenumbers", "pycountry", "ttkthemes", "Pillow"]
    with open(requirements_file, "w") as f:
        f.write('\n'.join(required_packages) + '\n')

    print("[+] Installo librerie richieste...")
    try:
        subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
        print("[✓] Librerie installate.\n")
    except Exception as e:
        print(f"⚠️ Installazione librerie fallita ({e}). Proseguo.")

    # ---------------------------
    # 4️⃣ Rilancio script nel venv
    # ---------------------------
    # Ottimizzazione del controllo: usiamo sys.prefix per rilevare l'ambiente virtuale.
    if sys.prefix != str(Path(sys.argv[0]).resolve().parent / f"Virtualenv{Path(sys.argv[0]).resolve().stem}"):
        print("[+] Riavvio lo script dentro il virtualenv...\n")
        os.execv(str(python_venv), [str(python_venv), str(script_path)] + sys.argv[1:])
    else:
        print("[✓] Script ora in esecuzione dentro il virtualenv.\n")


if sys.prefix != str(Path(sys.argv[0]).resolve().parent / f"Virtualenv{Path(sys.argv[0]).resolve().stem}"):
    setup_virtualenv()


# --- CONFIG / CONSTANTS ---
KEY = "e6358aeede676184b9fe702b30f4fd35e71744605e39d2181a34cede076b3c33"
SIG_KEY_VERSION = "4"
BASE_API = "https://i.instagram.com/api/v1"
APP_ID_WEBPROFILE = "936619743392459"
APP_ID_LOOKUP = "124024574287414"
session = requests.Session()
DEFAULT_HEADERS = {
    "User-Agent": "Instagram 292.0.0.17.111 Android (29/10; 420dpi; 1080x2340; generic; generic; generic; en_US)",
    "Accept-Language": "en-US",
}

# Mappa per i tipi di linea (usata in phone_info_osint)
LINE_TYPE_EMOJI = {
    PhoneNumberType.FIXED_LINE: "🏠 Fixed Line",
    PhoneNumberType.MOBILE: "📱 Mobile",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Fixed/Mobile",
    PhoneNumberType.TOLL_FREE: "🆓 Toll Free",
    PhoneNumberType.PREMIUM_RATE: "💰 Premium Rate",
    PhoneNumberType.VOIP: "🌐 VoIP",
    PhoneNumberType.UNKNOWN: "❓ Unknown"
}

# --- HELPERS (Funzioni di base) ---

def generate_signed_body(payload: dict) -> str:
    """Crea la firma HMAC-SHA256 richiesta dall'API mobile."""
    data_json = json.dumps(payload, separators=(",", ":"))
    sig = hmac.new(KEY.encode("utf-8"), data_json.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{sig}.{data_json}"

def pretty_phone_from_parts(country_code, phone_number):
    """Formatta un numero di telefono con il nome del paese."""
    try:
        raw = f"+{country_code}{phone_number}"
        pn = phonenumbers.parse(raw)
        cc = region_code_for_country_code(pn.country_code)
        country = pycountry.countries.get(alpha_2=cc)
        if country:
            return f"{raw} ({country.name})"
        return raw
    except Exception:
        return f"+{country_code}{phone_number}"

def download_image_to_bytes(url: str) -> bytes or None:
    """Scarica i dati binari di un'immagine da un URL."""
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        if 'image' in resp.headers.get('Content-Type', ''):
            return resp.content
    except Exception:
        return None

# MODIFICATA: Per salvare solo l'immagine, la gestione dei formati è nella GUI
def save_result_files_img_only(username, info_dict, output_path):
    """Salva l'immagine del profilo su file .jpg."""
    img_file = None
    try:
        if "Profile Picture Data" in info_dict and info_dict["Profile Picture Data"] is not None:
            image_bytes = info_dict["Profile Picture Data"]
            img_file = f"{output_path}_profile.jpg"
            with open(img_file, "wb") as img_f:
                img_f.write(image_bytes)
        
        return img_file
    except Exception as e:
        print(f"Errore durante il salvataggio dell'immagine: {e}")
        return None

# --- API FUNCTIONS (invariate) ---
def api_web_profile_info(username: str, sessionid: str = None):
    url = f"{BASE_API}/users/web_profile_info/?username={urllib.parse.quote_plus(username)}"
    headers = DEFAULT_HEADERS.copy()
    headers.update({"X-IG-App-ID": APP_ID_WEBPROFILE})
    cookies = {}
    if sessionid:
        cookies["sessionid"] = sessionid
    try:
        resp = session.get(url, headers=headers, cookies=cookies, timeout=15)
    except Exception as e:
        return {"Error": f"Request error: {e}"}
    if resp.status_code != 200:
        return {"Error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    try:
        j = resp.json()
    except Exception as e:
        return {"Error": f"JSON decode error: {e}"}
    user = j.get("data", {}).get("user")
    if not user:
        return {"Error": "No 'user' in response"}
    return user

def api_user_info_by_id(user_id: str, sessionid: str = None):
    url = f"{BASE_API}/users/{user_id}/info/"
    headers = DEFAULT_HEADERS.copy()
    headers.update({"X-IG-App-ID": APP_ID_WEBPROFILE})
    cookies = {}
    if sessionid:
        cookies["sessionid"] = sessionid
    try:
        resp = session.get(url, headers=headers, cookies=cookies, timeout=15)
    except Exception as e:
        return {"Error": f"Request error: {e}"}
    if resp.status_code != 200:
        return {"Error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    try:
        return resp.json().get("user", {})
    except Exception as e:
        return {"Error": f"JSON decode: {e}"}

def api_users_lookup(username: str):
    url = f"{BASE_API}/users/lookup/"
    payload = {
        "q": username,
        "skip_recovery": "1",
        "device_id": str(uuid.uuid4()),
        "guid": str(uuid.uuid4()),
        "_csrftoken": "missing"
    }
    signed = generate_signed_body(payload)
    data = {
        "signed_body": signed,
        "ig_sig_key_version": SIG_KEY_VERSION
    }
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-IG-App-ID": APP_ID_LOOKUP,
        "Accept": "*/*",
    })
    try:
        resp = session.post(url, headers=headers, data=data, timeout=15)
    except Exception:
        return {}
    if resp.status_code != 200:
        return {"_error_status": resp.status_code, "_error_text": resp.text[:500]}
    try:
        return resp.json()
    except Exception:
        return {}

# --- FUNZIONE RICERCA GLOBALE (Invariata nella logica di ricerca) ---

def username_info_global(username: str):
    """Esegue la ricerca dello username su diverse piattaforme social."""
    results = {}
    social_media = [
        {"url": "https://www.facebook.com/{}", "name": "Facebook", "icon": "🔵"},
        {"url": "https://www.twitter.com/{}", "name": "Twitter/X", "icon": "🐦"},
        {"url": "https://www.instagram.com/{}", "name": "Instagram", "icon": "📸"},
        {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn", "icon": "💼"},
        {"url": "https://www.github.com/{}", "name": "GitHub", "icon": "🐙"},
        {"url": "https://www.pinterest.com/{}", "name": "Pinterest", "icon": "📌"},
        {"url": "https://www.tumblr.com/{}", "name": "Tumblr", "icon": "🟣"},
        {"url": "https://www.youtube.com/@{}", "name": "YouTube", "icon": "🔴"},
        {"url": "https://soundcloud.com/{}", "name": "SoundCloud", "icon": "☁️"},
        {"url": "https://www.tiktok.com/@{}", "name": "TikTok", "icon": "🎵"},
        {"url": "https://www.medium.com/@{}", "name": "Medium", "icon": "✍️"},
        {"url": "https://www.quora.com/profile/{}", "name": "Quora", "icon": "❓"},
        {"url": "https://www.flickr.com/people/{}", "name": "Flickr", "icon": "📷"},
        {"url": "https://www.twitch.tv/{}", "name": "Twitch", "icon": "👾"},
        {"url": "https://www.dribbble.com/{}", "name": "Dribbble", "icon": "🏀"},
        {"url": "https://t.me/{}", "name": "Telegram", "icon": "✈️"},
        {"url": "https://bsky.app/profile/{}.bsky.social", "name": "BluSky", "icon": "🟦"}
    ]

    for site in social_media:
        url = site['url'].format(username)
        site_info = {"status": None, "url": None, "icon": site['icon']}
        try:
            response = requests.head(url, timeout=5, headers=DEFAULT_HEADERS)
            if response.status_code in [200, 301, 302]:
                site_info["status"] = "Found"
                site_info["url"] = url
            elif response.status_code == 404:
                 site_info["status"] = "Not Found (404)"
            else:
                 site_info["status"] = f"Manual check (HTTP {response.status_code})"
        except requests.RequestException:
             site_info["status"] = "Connection Error"
        except Exception:
             site_info["status"] = "Generic Error"
        
        results[site['name']] = site_info

    return results

# --- FUNZIONE RICERCA TELEFONO (Invariata) ---

def phone_info_osint(phone_number: str) -> dict:
    """Analizza il numero di telefono e fornisce informazioni OSINT di base."""
    if not phone_number.startswith('+'):
        return {"Error": "The number must include the international prefix (e.g. +39...)."}
    
    try:
        parsed = phonenumbers.parse(phone_number)
        
        if not is_possible_number(parsed):
             return {"Error": f"Invalid or impossible number: {phone_number}"}
        
        is_valid = is_valid_number(parsed)
        operator = carrier.name_for_number(parsed, "en") # Usiamo inglese per l'operatore
        line_type_raw = number_type(parsed)
        
        country_code = parsed.country_code
        region_code = region_code_for_country_code(country_code)
        
        country = pycountry.countries.get(alpha_2=region_code)
        country_name = country.name if country else region_code

        result = {
            "Number": phone_number,
            "Valid": '✅ Yes' if is_valid else '❌ No',
            "Possible": '✅ Yes' if is_possible_number(parsed) else '❌ No',
            "Country (Code)": f"{country_name} (+{country_code})",
            "Operator": operator if operator else "Not Available (NA)",
            "Line Type": LINE_TYPE_EMOJI.get(line_type_raw, "❓ Unclassified"),
            "Telegram Link": f"https://t.me/+{phone_number.lstrip('+')}",
            "WhatsApp Link": f"https://wa.me/{phone_number.lstrip('+')}"
        }
        
        return result

    except phonenumbers.NumberParseException as e:
        return {"Error": f"Number parsing error: {e}"}
    except Exception as e:
        return {"Error": f"Unknown error during analysis: {e}"}


# --- INSTAGRAM OSINT CLASS (Invariata) ---
class InstagramOSINT:
    def __init__(self):
        self.sessionid = None

    def set_sessionid(self, sessionid: str):
        self.sessionid = sessionid.strip() if sessionid else None
    
    def _fetch_profile_data(self, info_source: dict, username: str = None):
        result = {}
        
        result["Username"] = info_source.get("username") or info_source.get("pk")
        result["ID"] = info_source.get("id") or info_source.get("pk")
        result["Full Name"] = info_source.get("full_name")
        result["Biography"] = info_source.get("biography")
        result["Followers"] = info_source.get("edge_followed_by", {}).get("count") or info_source.get("follower_count")
        result["Following"] = info_source.get("edge_follow", {}).get("count") or info_source.get("following_count")
        result["Posts"] = info_source.get("edge_owner_to_timeline_media", {}).get("count")
        result["Media"] = info_source.get("media_count")
        result["Private"] = info_source.get("is_private")
        result["Verified"] = info_source.get("is_verified")
        profile_pic_url = info_source.get("profile_pic_url_hd") or info_source.get("profile_pic_url")
        result["Profile Pic URL"] = profile_pic_url

        if info_source.get("public_email"):
            result["Public Email"] = info_source.get("public_email")
        if info_source.get("public_phone_number"):
            cc = info_source.get("public_phone_country_code", "")
            pn = info_source.get("public_phone_number", "")
            result["Public Phone"] = pretty_phone_from_parts(cc, pn)
            
        if username:
            lookup = api_users_lookup(username)
            if lookup.get("_error_status"):
                result["Lookup Error"] = f"HTTP {lookup.get('_error_status')}: {lookup.get('_error_text')}"
            else:
                obf_email = lookup.get("obfuscated_email") or lookup.get("user", {}).get("obfuscated_email")
                obf_phone = lookup.get("obfuscated_phone") or lookup.get("user", {}).get("obfuscated_phone")
                if obf_email:
                    result["Obfuscated Email"] = obf_email
                if obf_phone:
                    result["Obfuscated Phone"] = obf_phone
                if lookup.get("message"):
                    result["Lookup Message"] = lookup.get("message")
        
        if profile_pic_url:
            image_data = download_image_to_bytes(profile_pic_url)
            result["Profile Picture Data"] = image_data
        else:
            result["Profile Picture Data"] = None

        return result
    
    def profile_by_username(self, username: str):
        u = api_web_profile_info(username, self.sessionid)
        if "Error" in u:
            return {"Error": u["Error"]}
        
        if u.get("id"):
            info_by_id = api_user_info_by_id(u["id"], self.sessionid)
            if isinstance(info_by_id, dict) and "Error" not in info_by_id:
                u.update(info_by_id)
        
        return self._fetch_profile_data(u, username=username)

    def profile_by_id(self, user_id: str):
        info = api_user_info_by_id(user_id, self.sessionid)
        if "Error" in info:
            return {"Error": info["Error"]}
            
        return self._fetch_profile_data(info, username=info.get("username"))

# --- TK GUI CLASS (Layout Aggiornato) ---

class CScorzaOSINTApp(ThemedTk):
    def __init__(self):
        try:
            super().__init__(theme='equilux')
        except:
             super().__init__(theme='clam')
             self.tk_setPalette(background='#2b2b2b', foreground='white', 
                                 selectBackground='#6495ED', selectForeground='white', 
                                 activeBackground='#454545', activeForeground='white')

        self.title("CScorza - OSINT Instagram")
        # Rimosso self.geometry("900x750") e self.resizable(True, True) qui.

        self.osint = InstagramOSINT()
        
        # INIZIALIZZAZIONE VARIABILI LOGO
        logo_img = None
        self.logo_small_header = None
        self.logo_header_image = None
        self.logo_side_ref = None # Nuovo riferimento per il logo a lato
        
        self._last_result = None
        self.profile_image_tk = None 
        self.output = None     
        self.image_label = None 
        self.target_entry = None 
        self.global_image_frame = None 
        self.global_image_refs = []  

        if Image and ImageTk:
            try:
                script_dir = Path(sys.argv[0]).resolve().parent
                # Percorso logo richiesto
                logo_path = script_dir / "Logo.gif"

                if logo_path.exists():
                    logo_img = Image.open(logo_path)
                    
                    logo_icon = logo_img.copy().resize((24, 24), Image.LANCZOS)
                    self.logo_icon_tk = ImageTk.PhotoImage(logo_icon)
                    self.iconphoto(True, self.logo_icon_tk) 
                    
                    # LOGO GRANDE (120x120) per la schermata di login e come logo a lato
                    # Modifica: Aumentato il resize da (80, 80) a (120, 120)
                    logo_large = logo_img.copy().resize((140, 120), Image.LANCZOS) 
                    self.logo_header_image = ImageTk.PhotoImage(logo_large)
                    
                    # Logo piccolo per l'header principale
                    logo_small = logo_img.copy().resize((48, 24), Image.LANCZOS)
                    self.logo_small_header = ImageTk.PhotoImage(logo_small)


            except Exception as e:
                # La variabile logo_img non viene usata qui, ma stampiamo l'errore per debug.
                print(f"Errore durante il caricamento del logo: {e}")

        # IMPOSTA LA FINESTRA A SCHERMO INTERO SUBITO ALL'AVVIO
        try:
            self.attributes('-fullscreen', True)
        except tk.TclError:
            # Fallback per la massimizzazione se fullscreen completo non è supportato
            self.state('zoomed') # Tenta la massimizzazione su sistemi che la supportano

        self._build_login_frame()

    def _build_login_frame(self):
        # COLORE PER LE SEZIONI GUIDA
        SECTION_COLOR = '#6495ED'
        
        # Rimuoviamo il relief dal login_container per un aspetto più pulito a schermo intero
        self.login_container = ttk.Frame(self, padding="30 20 30 20") # Rimosso relief=tk.RIDGE
        # Usiamo fill="both" e padx/pady a 0 per riempire l'intera finestra
        self.login_container.pack(expand=True, fill="both", padx=0, pady=0) 
        self.login_container.columnconfigure(0, weight=1)

        # 1. HEADER (Logo grande e Titolo)
        if self.logo_header_image:
            logo_label = ttk.Label(self.login_container, image=self.logo_header_image)
            logo_label.pack(pady=(0, 5))
            
            ttk.Label(self.login_container, text="CScorza Tools - Instagram OSINT",
                      font=("Arial", 18, "bold"), foreground=SECTION_COLOR).pack(pady=(0, 20))
        else:
            ttk.Label(self.login_container, text="🕵️ CScorza Tools - Instagram OSINT",
                      font=("Arial", 18, "bold"), foreground=SECTION_COLOR).pack(pady=(0, 20))


        # 2. SEZIONE LOGIN
        ttk.Label(self.login_container, text="Phase 1 — Enter your Instagram SessionID", 
                  font=("Arial", 14, "bold")).pack(pady=(5, 10))
        
        ttk.Label(self.login_container, text="❗ Optional SessionID: improves access to non-public info (e.g. email/phone).", 
                  font=("Arial", 10)).pack(pady=(0, 15))

        ses_frame = ttk.Frame(self.login_container)
        ses_frame.pack(fill="x", pady=5)
        
        ses_frame.columnconfigure(1, weight=1)
        ttk.Label(ses_frame, text="SessionID:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.session_entry = ttk.Entry(ses_frame, width=50, show="*")
        self.session_entry.grid(row=0, column=1, sticky="ew")
        
        ttk.Button(ses_frame, text="📁 Load from file", command=self._load_session_from_file).grid(row=0, column=2, padx=10)

        ttk.Button(self.login_container, text="➡️ Load and Start Search", 
                    command=self._on_login_continue, 
                    cursor="hand2").pack(pady=15, ipadx=10, ipady=5)
                        
        
        # 3. MINI GUIDA E COPYRIGHT
        ttk.Separator(self.login_container, orient='horizontal').pack(fill='x', pady=15)
        
        # Mini Guida (RE-IMPLEMENTATA CON ttk.Label)
        guide_frame = ttk.Frame(self.login_container)
        guide_frame.pack(fill='x', pady=5)
        
        ttk.Label(guide_frame, text="🚀 Script Functionality Guide:", 
                  font=("Arial", 11, "bold"), foreground=SECTION_COLOR).pack(anchor='w', pady=(0, 5))
        
        # Contenitore per le voci della guida (uso un frame interno per padding)
        guide_content_frame = ttk.Frame(guide_frame, padding=(10, 5))
        guide_content_frame.pack(fill='x')
        
        guide_items = [
            ("Instagram Actions:", "Retrieve public/obfuscated data (User Info, ID Info) and open the profile in a browser (Explore Profile)."),
            ("Phone Search:", "Analyzes the international format number (+XX...) for validity, operator, line type, and link generation (Telegram/WhatsApp)."),
            ("Username Search:", "Cross-checks the username's existence across over 15 major social media platforms, providing direct links."),
            ("Google CSE:", "Uses a Custom Google Search Engine to perform deep, site-specific searches with the input query."),
            ("SessionID Persistence:", "Your SessionID is securely saved locally in `sessionid.txt` for automatic loading on future runs (optional)."),
        ]
        
        for i, (title, desc) in enumerate(guide_items):
            # Titolo in bold
            ttk.Label(guide_content_frame, text=f"• {title}", font=("Arial", 12, "bold")).grid(row=i, column=0, sticky='nw')
            # Descrizione
            ttk.Label(guide_content_frame, text=desc, font=("Arial", 12), wraplength=450).grid(row=i, column=1, sticky='nw', padx=(5, 0))
            guide_content_frame.grid_columnconfigure(1, weight=1)

        
        # Come recuperare il SessionID
        ttk.Label(guide_frame, text="🔑 How to retrieve SessionID:", 
                  font=("Arial", 12, "bold"), foreground=SECTION_COLOR).pack(anchor='w', pady=(10, 0))
        
        ttk.Label(guide_frame, text="1. Log into Instagram on a web browser (or mobile browser developer tools).\n2. Open Developer Tools (F12) > Application/Storage > Cookies.\n3. Copy the value associated with the cookie named 'sessionid'.", 
                  font=("Arial", 12)).pack(anchor='w', padx=5)


        # 4. COPYRIGHT E RIFERIMENTI (Ristrutturato per includere l'immagine a lato)
        ttk.Separator(self.login_container, orient='horizontal').pack(fill='x', pady=15)
        
        # Nuovo contenitore con griglia 2 colonne: Riferimenti (Col. 0) e Logo (Col. 1)
        ref_and_logo_frame = ttk.Frame(self.login_container)
        ref_and_logo_frame.pack(fill='x', expand=True)
        
        # Modifica: Aumentiamo il peso della colonna 0 (testo) e diminuiamo quello del logo
        # per forzare il logo a stare più a sinistra possibile nel suo spazio.
        ref_and_logo_frame.columnconfigure(0, weight=4) 
        ref_and_logo_frame.columnconfigure(1, weight=1) 
        
        # Riferimenti (Colonna 0)
        ref_frame = ttk.Frame(ref_and_logo_frame)
        ref_frame.grid(row=0, column=0, sticky='nw') 
        
        ttk.Label(ref_frame, text="© CScorza - Indagini Telematiche 2025 | OSINT References", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 5))
        
        ref_data = [
            ("✈️ Telegram Channel:", "https://t.me/CScorzaOSINT"),
            ("🌐 Web Site:", "https://cscorza.github.io/CScorza"),
            ("🐦 Twitter/X:", "@CScorzaOSINT"),
            ("🐙 GitHub:", "https://github.com/CScorza"),
            ("📧 Contact:", "cscorzaosint@protonmail.com"),
            ("₿ BTC:", "bc1qfn9kynt7k26eaxk4tc67q2hjuzhfcmutzq2q6a"),
            ("💎 TON:", "UQBtLB6m-7q8j9Y81FeccBEjccvl34Ag5tWaUD")
        ]
        
        # Usa una griglia per allineare chiave e valore per i riferimenti
        ref_grid_frame = ttk.Frame(ref_frame)
        ref_grid_frame.pack(fill='x', padx=5)
        
        for i, (key, value) in enumerate(ref_data):
            ttk.Label(ref_grid_frame, text=key, font=("Arial", 12, "bold")).grid(row=i, column=0, sticky='w', padx=(5, 0))
            
            link_label = ttk.Label(ref_grid_frame, text=value, font=("Arial", 12), foreground=SECTION_COLOR, cursor="hand2")
            link_label.grid(row=i, column=1, sticky='w', padx=(5, 0))
            
            # Funzione lambda per aprire il link/email/wallet
            def open_link_or_copy(val):
                if val.startswith("http"):
                    webbrowser.open_new(val)
                elif val.startswith("@") or val.startswith("bc1") or val.startswith("UQBtL"):
                    self.clipboard_clear()
                    self.clipboard_append(val)
                    messagebox.showinfo("Copied", f"Value copied to clipboard: {val}")
                elif val.startswith("cscorzaosint"):
                    webbrowser.open_new(f"mailto:{val}")
            
            link_label.bind("<Button-1>", lambda e, val=value: open_link_or_copy(val))

        ref_grid_frame.columnconfigure(1, weight=1)

        # Logo a lato (Colonna 1)
        if self.logo_header_image:
            logo_label_side = ttk.Label(ref_and_logo_frame, image=self.logo_header_image, padding=10)
            # Modifica: Usiamo 'nw' (Nord-Ovest) e rimuoviamo il padx per spingerlo a sinistra
            logo_label_side.grid(row=0, column=1, sticky='nw', padx=(0, 0)) 
            # Mantiene il riferimento per prevenire il garbage collection
            self.logo_side_ref = self.logo_header_image 
        else:
            ttk.Label(ref_and_logo_frame, text="[Logo non caricato]", font=("Arial", 10)).grid(row=0, column=1, sticky='nw', padx=(0, 0))


    def _load_session_from_file(self):
        path = "sessionid.txt"
        try:
            with open(path, "r", encoding="utf-8") as f:
                val = f.read().strip()
            self.session_entry.delete(0, tk.END)
            self.session_entry.insert(0, val)
            messagebox.showinfo("✅ OK", f"SessionID loaded from file {path}.")
        except FileNotFoundError:
            messagebox.showwarning("⚠️ Warning", f"No file {path} found.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Cannot read file: {e}")

    def _on_login_continue(self):
        sessionid = self.session_entry.get().strip()
        if sessionid:
            self.osint.set_sessionid(sessionid)
            try:
                with open("sessionid.txt", "w", encoding="utf-8") as f:
                    f.write(sessionid)
            except Exception as e:
                print(f"[!] Cannot save sessionid: {e}")
        
        self.login_container.destroy()
        
        # AVVIA A SCHERMO INTERO (Già impostato in __init__)
        # Riabilito la massimizzazione, anche se il fullscreen fallisce, per coerenza
        try:
            self.attributes('-fullscreen', True)
        except tk.TclError:
            self.state('zoomed') 

        self._build_search_frame()

    def _open_in_browser(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Error", "Enter a username or ID to explore.")
            return
        if target.isdigit():
            messagebox.showinfo("Info", "Opening profile by ID is not direct. Opening Instagram search page.")
            webbrowser.open("https://instagram.com/explore/people/suggested/")
        else:
            webbrowser.open(f"https://instagram.com/{target}")
            
    def _open_google_cse(self):
        query = self.target_entry.get().strip()
        if not query:
            messagebox.showwarning("Error", "Enter a query (username, ID, or phone number) to search on Google CSE.")
            return
        
        # URL specifico per la Ricerca Personalizzata di Google (Google CSE)
        base_url = "https://cse.google.com/cse"
        cx = "d28c23ec014bd4cca" # Identificativo della tua Custom Search Engine
        url = f"{base_url}?cx={cx}#gsc.tab=0&gsc.q={urllib.parse.quote_plus(query)}"
        webbrowser.open_new(url)

    def _clear_output(self):
        """Pulisce la barra di input, l'output testuale e le anteprime."""
        self.target_entry.delete(0, tk.END)
        self.output.delete("1.0", tk.END)
        self._last_result = None
        
        # Pulisce le immagini
        self.image_label.config(image='', text="No Results")
        self.profile_image_tk = None
        self._display_global_images({})
        messagebox.showinfo("Clear", "Output and search fields cleared.")

    def _open_profile_pic(self, event):
        if self._last_result and self._last_result[1].get("Profile Pic URL"):
            webbrowser.open(self._last_result[1]["Profile Pic URL"])
        elif self._last_result:
            messagebox.showinfo("Info", "Profile Pic URL not found.")


    def _build_search_frame(self):
        # COLORE UNIFORME PER LE ETICHETTE DELLE CATEGORIE
        CATEGORY_COLOR = '#6495ED' 

        main_frame = ttk.Frame(self, padding="10 10 10 0")
        main_frame.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        
        # Header e status (Tradotto)
        if hasattr(self, 'logo_small_header'):
            header_label = ttk.Label(main_frame, text="CScorza - OSINT Instagram", 
                                     font=("Arial", 18, "bold"), foreground=CATEGORY_COLOR,
                                     image=self.logo_small_header, compound="left", padding=(0,0,8,0))
            header_label.pack(pady=(0, 5))
        else:
            ttk.Label(main_frame, text="🔍 CScorza - OSINT Instagram", font=("Arial", 18, "bold"), foreground=CATEGORY_COLOR).pack(pady=(0, 5))

        ttk.Label(main_frame, text=f"SessionID Status: {'✅ ACTIVE' if self.osint.sessionid else '❌ NOT ACTIVE'}", 
                  font=("Arial", 10, "italic")).pack(pady=(0, 10))

        # --- INPUT E BARRA DI RICERCA (Frame Superiore) ---
        input_wrapper = ttk.Frame(main_frame)
        input_wrapper.pack(fill="x", pady=(0, 10)) 
        input_wrapper.columnconfigure(1, weight=1)
        
        # Etichetta con suggerimento per il prefisso (Tradotto)
        ttk.Label(input_wrapper, text="Target (Username / ID / Phone) (e.g. +39 for numbers):", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Barra di input
        self.target_entry = ttk.Entry(input_wrapper)
        self.target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # --- CONTENITORE BOTTONI E RIORGANIZZAZIONE GRAFICA (V12) ---
        button_container_outer = ttk.Frame(main_frame)
        button_container_outer.pack(fill="x", pady=(0, 10))
        
        # Sotto-Frame per i Bottoni (layout principale)
        button_container = ttk.Frame(button_container_outer)
        button_container.pack(fill="x")
        
        # Centratura implicita usando la griglia
        button_container.columnconfigure(0, weight=1) # Colonna IG
        button_container.columnconfigure(1, weight=1) # Colonna Global

        # 1. Gruppo Instagram (Colonna 0)
        ig_wrapper = ttk.Frame(button_container)
        ig_wrapper.grid(row=0, column=0, sticky="n", padx=(0, 10)) 
        
        # A. Etichetta OSINT Instagram
        ttk.Label(ig_wrapper, text="OSINT Instagram", font=("Arial", 10, "bold"), foreground=CATEGORY_COLOR).pack(pady=(0, 3))
        
        # B. Bottoni di Ricerca IG (User Info, ID Info)
        ig_search_frame = ttk.Frame(ig_wrapper)
        ig_search_frame.pack(pady=(0, 5))
        ttk.Label(ig_search_frame, text="Actions:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
        ttk.Button(ig_search_frame, text="User Info", command=self._on_user_info, cursor="hand2").pack(side="left", padx=(5, 5))
        ttk.Button(ig_search_frame, text="ID Info", command=self._on_id_info, cursor="hand2").pack(side="left", padx=(5, 5))
        
        # C. Bottone Explore Profile (Centrato sotto le azioni IG)
        explore_wrapper = ttk.Frame(ig_wrapper)
        explore_wrapper.pack(pady=(5, 0))
        ttk.Button(explore_wrapper, text="🌐 Explore Profile", command=self._open_in_browser, cursor="hand2").pack()
        
        
        # 2. Gruppo Global Search (Colonna 1)
        global_wrapper = ttk.Frame(button_container)
        global_wrapper.grid(row=0, column=1, sticky="n", padx=(10, 0))
        
        # A. Etichetta Global Search (Centrata & Colore uniforme)
        ttk.Label(global_wrapper, text="Global Search:", font=("Arial", 10, "bold"), foreground=CATEGORY_COLOR).pack(pady=(0, 3))
        
        # B. Bottoni Phone Search / Username Search (Centrati)
        global_search_frame = ttk.Frame(global_wrapper)
        global_search_frame.pack(pady=(0, 5)) 
        ttk.Button(global_search_frame, text="📞 Phone Search", command=self._on_phone_info, cursor="hand2").pack(side="left", padx=(5, 5))
        ttk.Button(global_search_frame, text="🌐 Username Search", command=self._on_global_search, cursor="hand2").pack(side="left", padx=(5, 5))

        # C. Nuovo bottone Google CSE (Centrato sotto i due bottoni globali)
        google_wrapper = ttk.Frame(global_wrapper)
        google_wrapper.pack(pady=(5, 0))
        ttk.Button(google_wrapper, text="🔍 Search Google CSE", command=self._open_google_cse, cursor="hand2").pack()


        # --- Frame per Anteprima e Output (Invariato) ---
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill="both", expand=True, pady=(5, 12))
        result_frame.columnconfigure(1, weight=1)
        result_frame.rowconfigure(0, weight=1)

        # 1. Pannello Immagine (a sinistra)
        image_panel = ttk.Frame(result_frame, width=200)
        image_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Sotto-Frame per l'immagine Instagram
        ig_image_wrapper = ttk.Frame(image_panel)
        ig_image_wrapper.pack(pady=(0, 5))
        ttk.Label(ig_image_wrapper, text="Instagram Profile (Click to open)", font=("Arial", 10, "bold")).pack()
        
        # Frame contenitore fisso 180x180 per l'immagine IG
        ig_size_frame = ttk.Frame(ig_image_wrapper, width=180, height=180)
        ig_size_frame.pack()
        ig_size_frame.pack_propagate(False) # Impedisce al contenuto di ridimensionarlo
        
        self.image_label = ttk.Label(ig_size_frame, relief=tk.SOLID, borderwidth=1, text="No Results", anchor="center")
        self.image_label.pack(fill="both", expand=True) # Riempie il frame contenitore
        self.image_label.bind("<Button-1>", self._open_profile_pic)

        # Nuovo Frame per le immagini/icone Globali (scorrimento verticale)
        self.global_image_frame = ttk.Frame(image_panel, width=200)
        self.global_image_frame.pack(fill="x", pady=(10, 0))


        # 2. Output Box (a destra)
        self.output = scrolledtext.ScrolledText(result_frame, width=70, height=30, font=("Consolas", 10), 
                                                 bg='#1c1c1c', fg='lightgrey', insertbackground='white')
        self.output.grid(row=0, column=1, sticky="nsew")
        self.output.tag_config('highlight', foreground='#ADD8E6')
        self.output.tag_config('error', foreground='#FA8072')
        self.output.tag_config('obfuscated', foreground='#FFD700')
        self.output.tag_config('link', foreground='#00BFFF', underline=1)

        # Options (in fondo)
        ops_frame = ttk.Frame(main_frame, padding="0 0 0 5")
        ops_frame.pack(fill="x")
        # Pulsante di pulizia ora chiama la funzione _clear_output
        ttk.Button(ops_frame, text="🗑️ Clear All", command=self._clear_output, cursor="hand2").pack(side="right") 
        ttk.Button(ops_frame, text="💾 Save to File", command=self._save_last_result, cursor="hand2").pack(side="right", padx=10)


    def _display_global_images(self, results):
        """Visualizza le icone dei social trovati sotto l'immagine di Instagram."""
        
        for widget in self.global_image_frame.winfo_children():
            widget.destroy()
        self.global_image_refs.clear()
        
        found_widgets = []
        
        for site, info in results.items():
            # Nota: Ricerca IG è già coperta dall'immagine principale, la saltiamo qui
            if info['status'] == "Found" and Image and ImageTk and site != "Instagram":
                
                icon_text = info['icon']
                link = info['url']
                
                icon_wrapper = ttk.Frame(self.global_image_frame)
                
                icon_label = ttk.Label(icon_wrapper, text=icon_text, font=("Arial", 24), cursor="hand2")
                icon_label.pack(padx=2, pady=2)
                
                site_name_label = ttk.Label(icon_wrapper, text=site, font=("Arial", 7))
                site_name_label.pack()

                def open_link(url_to_open):
                    return lambda event: webbrowser.open_new(url_to_open)
                
                icon_label.bind("<Button-1>", open_link(link))
                
                found_widgets.append(icon_wrapper)

        for i, widget in enumerate(found_widgets):
            widget.grid(row=i // 4, column=i % 4, padx=5, pady=5)


    def _on_phone_info(self):
        phone_number = self.target_entry.get().strip()
        if not phone_number or not phone_number.startswith('+'):
            messagebox.showwarning("Error", "The number must include the international prefix (e.g. +39...).")
            return

        self.output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 📞 Starting phone number analysis: {phone_number}\n")
        self.output.see(tk.END)
        
        info = phone_info_osint(phone_number)
        
        self.output.insert(tk.END, "\n" + "="*40 + "\n")

        if "Error" in info:
            self.output.insert(tk.END, f"❌ Analysis Error: {info.get('Error')}\n", 'error')
        else:
            self.output.insert(tk.END, f"✅ Phone Analysis Result:\n")
            
            for k, v in info.items():
                tag = 'highlight' if "Link" not in k else 'link'
                self.output.insert(tk.END, f"{k}: ", tag)
                self.output.insert(tk.END, f"{v}\n")
        
        self.output.insert(tk.END, "="*40 + "\n\n")
        self.output.see(tk.END)
        
        self.output.tag_bind('link', '<Button-1>', self._open_global_link)

    def _on_global_search(self):
        username = self.target_entry.get().strip()
        if not username or username.isdigit():
            messagebox.showwarning("Error", "Enter a valid username (not a numeric ID) for the global search.")
            return

        self.output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 Starting global username search: {username}\n")
        self.output.see(tk.END)
        
        results = username_info_global(username)
        
        # 1. Visualizza le icone/immagini
        self._display_global_images(results)
        
        # 2. Visualizza i risultati testuali
        self.output.insert(tk.END, "\n" + "="*40 + "\n")
        self.output.insert(tk.END, f"🌐 Global Search Results for: {username}\n")
        
        found_links = []
        
        for site, info in results.items():
            status = info['status']
            link = info['url']
            
            self.output.insert(tk.END, f"{info['icon']} {site}: ")
            
            if status == "Found":
                self.output.insert(tk.END, link + "\n", 'link')
                found_links.append(link)
            elif "Not Found" in status:
                self.output.insert(tk.END, status + "\n", 'error')
            else:
                self.output.insert(tk.END, status + "\n")


        self.output.insert(tk.END, "="*40 + "\n")
        self.output.insert(tk.END, f"Sites found: {len(found_links)} / {len(results)}\n\n")
        self.output.see(tk.END)
        
        self.output.tag_bind('link', '<Button-1>', self._open_global_link)

    def _open_global_link(self, event):
        """Gestisce il click sui link generati dalla ricerca globale o del telefono."""
        try:
            index = self.output.index("@%s,%s" % (event.x, event.y))
            tag_ranges = self.output.tag_ranges('link')
            
            for start, end in zip(tag_ranges[0::2], tag_ranges[1::2]):
                if self.output.compare(start, '<=', index) and self.output.compare(index, '<', end):
                    url = self.output.get(start, end).strip()
                    # Estrarre solo l'URL se c'è un'etichetta prima (come nei risultati del telefono)
                    if url.startswith("Telegram Link: ") or url.startswith("WhatsApp Link: "):
                        url = url.split(": ", 1)[-1]
                        
                    webbrowser.open_new(url)
                    return
        except Exception as e:
            messagebox.showerror("Link Error", "Could not open the selected URL.")

    def _display_result(self, info: dict):
        # 1. Gestione Anteprima Immagine INSTAGRAM
        self.image_label.configure(image='', text="Loading...")
        self.profile_image_tk = None
        
        if Image and ImageTk and info.get("Profile Picture Data"):
            try:
                image_data = info["Profile Picture Data"]
                img = Image.open(BytesIO(image_data))
                
                size = 180
                img.thumbnail((size, size))
                
                self.profile_image_tk = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.profile_image_tk, text="")
                self.image_label.image = self.profile_image_tk
            except Exception as e:
                self.image_label.config(text="Preview Error", font=("Arial", 10))
                print(f"Image loading error: {e}")
        else:
            self.image_label.config(text="No Preview/Pillow missing", font=("Arial", 10))
            
        # 2. Pulisci la lista delle immagini globali quando si esegue una nuova ricerca IG
        self._display_global_images({}) 

        # 3. Gestione Output di Testo (Instagram)
        self.output.insert(tk.END, "\n" + "="*40 + "\n")
        if "Error" in info:
            self.output.insert(tk.END, f"❌ Error: {info.get('Error')}\n")
            self.output.insert(tk.END, "="*40 + "\n")
            return
        
        self.output.insert(tk.END, "✅ Result Found (Instagram):\n")
        
        keys_preferred = [
            "Username", "ID", "PK", "Full Name", "Biography",
            "Followers", "Following", "Posts", "Media",
            "Private", "Verified", "Profile Pic URL",
            "Public Email", "Public Phone",
            "Obfuscated Email", "Obfuscated Phone",
            "Lookup Message", "Lookup Error"
        ]

        for k in keys_preferred:
            if k in info:
                tag = 'highlight'
                if "Obfuscated" in k or "Public" in k:
                    tag = 'obfuscated'
                elif "Error" in k:
                    tag = 'error'
                
                self.output.insert(tk.END, f"{k}: ", tag)
                self.output.insert(tk.END, f"{info[k]}\n")
                
        for k, v in info.items():
            if k not in keys_preferred and k != "Profile Picture Data":
                self.output.insert(tk.END, f"{k}: {v}\n")
                
        self.output.insert(tk.END, "="*40 + "\n\n")
        self.output.see(tk.END)


    def _save_last_result(self):
        """Salva l'ultimo risultato in formato JSON, TXT o CSV/Excel con dialogo di salvataggio."""
        if not self._last_result:
            messagebox.showinfo("Info", "No results to save.")
            return

        username, info_dict = self._last_result
        
        # Definisce i formati disponibili nel dialogo
        file_types = [
            ('JSON File', '*.json'),
            ('Text File', '*.txt'),
            ('CSV File (Excel compatible)', '*.csv'),
            ('All Files', '*.*'),
        ]
        
        # Apre la finestra di dialogo per il salvataggio
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=f"{username}_osint",
            filetypes=file_types,
            title="Save OSINT Results"
        )

        if not save_path:
            return # Utente ha annullato

        file_format = os.path.splitext(save_path)[1].lower()
        
        # Dati da salvare (escludendo i dati binari dell'immagine)
        data_to_save = {k: v for k, v in info_dict.items() if k != "Profile Picture Data"}
        
        try:
            if file_format == '.json':
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                message = f"Results saved successfully in JSON to:\n{save_path}"
                
            elif file_format == '.csv':
                # Converti i dati in formato CSV (due colonne: Key, Value)
                with open(save_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Key", "Value"])
                    for k, v in data_to_save.items():
                        writer.writerow([k, str(v).replace('\n', ' ')]) # Rimuove newline per CSV pulito
                message = f"Results saved successfully in CSV (Excel) to:\n{save_path}"
                
            elif file_format == '.txt' or file_format == '.doc': # Salvataggio in formato TXT/DOC leggibile
                with open(save_path, 'w', encoding='utf-8') as f:
                    for k, v in data_to_save.items():
                        f.write(f"{k}: {v}\n")
                message = f"Results saved successfully in Text/DOC format to:\n{save_path}"
                
            else:
                raise ValueError("Unsupported file format selected.")

            # Salvataggio dell'immagine (se presente)
            img_file = save_result_files_img_only(username, info_dict, save_path.rsplit('.', 1)[0])
            if img_file:
                message += f"\nProfile image also saved to:\n{img_file}"
                
            messagebox.showinfo("✅ Save Successful", message)

        except Exception as e:
            messagebox.showerror("❌ Save Error", f"An error occurred while saving the file: {e}")


    def _on_user_info(self):
        username = self.target_entry.get().strip()
        if not username:
            messagebox.showwarning("Error", "Enter a username.")
            return
        self.output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ➡️ Requesting user info for: {username}\n")
        self.output.see(tk.END)
        info = self.osint.profile_by_username(username)
        self._last_result = (username, info)
        self._display_result(info)
        

    def _on_id_info(self):
        val = self.target_entry.get().strip()
        if not val or not val.isdigit():
            messagebox.showwarning("Error", "Enter a numeric ID.")
            return
        
        self.output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ➡️ Requesting ID info for: {val}\n")
        self.output.see(tk.END)
        info = self.osint.profile_by_id(val)
        self._last_result = (val, info)
        self._display_result(info)


# --- MAIN ---

def main():
    app = CScorzaOSINTApp()
    app.mainloop()

if __name__ == "__main__":
    main()
