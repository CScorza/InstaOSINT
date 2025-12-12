#!/usr/bin/env python3
# CScorza - OSINT Instagram (GUI + Email & Phone) - FINAL HARMONIZED
# Fix: History Column now auto-expands and centers content (No empty spaces)

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
import threading 

# --- CONFIGURAZIONE COLORI ---
BG_COLOR = "#0e0e0e"
FG_COLOR = "white"
ACCENT_COLOR = "#6495ED"

# --- SETUP VARIABILI MODULI ---
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
Menu = None 

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog, Menu
    import webbrowser
    import phonenumbers
    from phonenumbers.phonenumberutil import region_code_for_country_code
    from phonenumbers import carrier, number_type, PhoneNumberType, is_possible_number, is_valid_number
    import pycountry
    from PIL import Image, ImageTk, ImageDraw 
    from ttkthemes import ThemedTk
except ImportError:
    pass 

# --- SETUP VIRTUALENV ---
def setup_virtualenv():
    script_path = Path(sys.argv[0]).resolve()
    script_dir = script_path.parent
    script_name = script_path.stem
    env_name = f"Virtualenv{script_name}"
    venv_path = script_dir / env_name
    requirements_file = script_dir / "requirements.txt"

    try:
        import tkinter
    except ModuleNotFoundError:
        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "python3-tk"], check=True)
        except Exception:
            pass

    try:
        pkg_installed = subprocess.run(["dpkg", "-s", "python3-venv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except FileNotFoundError:
        pkg_installed = True 

    if not pkg_installed:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "python3-venv"], check=True)

    pip_path = venv_path / "bin" / "pip"
    python_venv = venv_path / "bin" / "python"

    if not venv_path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    required_packages = ["requests", "phonenumbers", "pycountry", "ttkthemes", "Pillow"]
    with open(requirements_file, "w") as f:
        f.write('\n'.join(required_packages) + '\n')

    try:
        subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
    except Exception:
        pass

    if sys.prefix != str(Path(sys.argv[0]).resolve().parent / f"Virtualenv{Path(sys.argv[0]).resolve().stem}"):
        os.execv(str(python_venv), [str(python_venv), str(script_path)] + sys.argv[1:])

if sys.prefix != str(Path(sys.argv[0]).resolve().parent / f"Virtualenv{Path(sys.argv[0]).resolve().stem}"):
    setup_virtualenv()


# --- CONFIG / CONSTANTS ---
KEY = "e6358aeede676184b9fe702b30f4fd35e71744605e39d2181a34cede076b3c33"
SIG_KEY_VERSION = "4"
BASE_API = "https://i.instagram.com/api/v1"
APP_ID_WEBPROFILE = "936619743392459"
APP_ID_LOOKUP = "124024574287414"
session = requests.Session()

# HEADERS
IG_HEADERS = {
    "User-Agent": "Instagram 292.0.0.17.111 Android (29/10; 420dpi; 1080x2340; generic; generic; generic; en_US)",
    "Accept-Language": "en-US",
}
WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US",
}

LINE_TYPE_EMOJI = {
    PhoneNumberType.FIXED_LINE: "🏠 Fixed Line",
    PhoneNumberType.MOBILE: "📱 Mobile",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Fixed/Mobile",
    PhoneNumberType.TOLL_FREE: "🆓 Toll Free",
    PhoneNumberType.PREMIUM_RATE: "💰 Premium Rate",
    PhoneNumberType.VOIP: "🌐 VoIP",
    PhoneNumberType.UNKNOWN: "❓ Unknown"
}

# --- HELPERS ---

def generate_signed_body(payload: dict) -> str:
    data_json = json.dumps(payload, separators=(",", ":"))
    sig = hmac.new(KEY.encode("utf-8"), data_json.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{sig}.{data_json}"

def pretty_phone_from_parts(country_code, phone_number):
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
    try:
        resp = session.get(url, timeout=5, headers=WEB_HEADERS)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        return None

def save_result_files_img_only(username, info_dict, output_path):
    img_file = None
    try:
        if "Profile Picture Data" in info_dict and info_dict["Profile Picture Data"] is not None:
            image_bytes = info_dict["Profile Picture Data"]
            img_file = f"{output_path}_profile.jpg"
            with open(img_file, "wb") as img_f:
                img_f.write(image_bytes)
        return img_file
    except Exception as e:
        print(f"Errore salvataggio immagine: {e}")
        return None

# --- API FUNCTIONS ---
def api_web_profile_info(username: str, sessionid: str = None):
    url = f"{BASE_API}/users/web_profile_info/?username={urllib.parse.quote_plus(username)}"
    headers = IG_HEADERS.copy()
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
    headers = IG_HEADERS.copy()
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

def api_users_lookup(username: str, sessionid: str = None):
    url = f"{BASE_API}/users/lookup/"
    payload = {
        "q": username, "skip_recovery": "1",
        "device_id": str(uuid.uuid4()), "guid": str(uuid.uuid4()),
        "_csrftoken": "missing"
    }
    signed = generate_signed_body(payload)
    data = {"signed_body": signed, "ig_sig_key_version": SIG_KEY_VERSION}
    headers = IG_HEADERS.copy()
    headers.update({
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-IG-App-ID": APP_ID_LOOKUP,
        "Accept": "*/*",
    })
    cookies = {}
    if sessionid:
        cookies["sessionid"] = sessionid
    try:
        resp = session.post(url, headers=headers, data=data, cookies=cookies, timeout=15)
    except Exception:
        return {}
    if resp.status_code != 200:
        return {"_error_status": resp.status_code, "_error_text": resp.text[:500]}
    try:
        return resp.json()
    except Exception:
        return {}

# --- FUNZIONE RICERCA GLOBALE ---
def username_info_global(username: str):
    results = {}
    social_media = [
        {"url": "https://www.facebook.com/{}", "name": "Facebook", "icon": "🔵"},
        {"url": "https://www.twitter.com/{}", "name": "Twitter/X", "icon": "🐦"},
        {"url": "https://www.instagram.com/{}", "name": "Instagram", "icon": "📸"},
        {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn", "icon": "💼"},
        {"url": "https://www.github.com/{}", "name": "GitHub", "icon": "🐙"},
        {"url": "https://www.tiktok.com/@{}", "name": "TikTok", "icon": "🎵"},
        {"url": "https://www.youtube.com/@{}", "name": "YouTube", "icon": "🔴"},
        {"url": "https://t.me/{}", "name": "Telegram", "icon": "✈️"},
        {"url": "https://bsky.app/profile/{}.bsky.social", "name": "BluSky", "icon": "🟦"}
    ]
    for site in social_media:
        url = site['url'].format(username)
        site_info = {"status": None, "url": None, "icon": site['icon'], "image_url": None}
        try:
            response = requests.get(url, timeout=3, headers=WEB_HEADERS)
            if response.status_code in [200, 301, 302]:
                site_info["status"] = "Found"
                site_info["url"] = url
                html = response.text
                match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                if match: site_info["image_url"] = match.group(1)
                else:
                    match_tw = re.search(r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                    if match_tw: site_info["image_url"] = match_tw.group(1)
            elif response.status_code == 404:
                 site_info["status"] = "Not Found (404)"
            else:
                 site_info["status"] = f"Manual check ({response.status_code})"
        except:
             site_info["status"] = "Generic Error"
        results[site['name']] = site_info
    return results

# --- FUNZIONE RICERCA TELEFONO ---
def phone_info_osint(phone_number: str) -> dict:
    if not phone_number.startswith('+'):
        return {"Error": "The number must include the international prefix (e.g. +39...)."}
    try:
        parsed = phonenumbers.parse(phone_number)
        if not is_possible_number(parsed):
             return {"Error": f"Invalid or impossible number: {phone_number}"}
        is_valid = is_valid_number(parsed)
        operator = carrier.name_for_number(parsed, "en")
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


# --- INSTAGRAM OSINT CLASS ---
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
            lookup = api_users_lookup(username, self.sessionid)
            if not lookup.get("_error_status"):
                obf_email = lookup.get("obfuscated_email") or lookup.get("user", {}).get("obfuscated_email")
                obf_phone = lookup.get("obfuscated_phone") or lookup.get("user", {}).get("obfuscated_phone")
                if obf_email: result["Obfuscated Email"] = obf_email
                if obf_phone: result["Obfuscated Phone"] = obf_phone
                if lookup.get("message"): result["Lookup Message"] = lookup.get("message")
        
        if profile_pic_url:
            image_data = download_image_to_bytes(profile_pic_url)
            result["Profile Picture Data"] = image_data
        else:
            result["Profile Picture Data"] = None
        return result
    
    def profile_by_username(self, username: str):
        u = api_web_profile_info(username, self.sessionid)
        if "Error" in u: return {"Error": u["Error"]}
        if u.get("id"):
            info_by_id = api_user_info_by_id(u["id"], self.sessionid)
            if isinstance(info_by_id, dict) and "Error" not in info_by_id:
                u.update(info_by_id)
        return self._fetch_profile_data(u, username=username)

    def profile_by_id(self, user_id: str):
        info = api_user_info_by_id(user_id, self.sessionid)
        if "Error" in info: return {"Error": info["Error"]}
        return self._fetch_profile_data(info, username=info.get("username"))

# --- TK GUI CLASS ---

class CScorzaOSINTApp(ThemedTk):
    def __init__(self):
        try:
            super().__init__(theme='equilux')
        except:
             super().__init__(theme='clam')
             self.tk_setPalette(background=BG_COLOR, foreground=FG_COLOR, 
                                 selectBackground=ACCENT_COLOR, selectForeground='white', 
                                 activeBackground='#2a2a2a', activeForeground='white')

        self.title("CScorza - OSINT Instagram")
        
        # Geometria Adattiva
        self.resizable(True, True) 
        self.minsize(500, 600)

        self.osint = InstagramOSINT()
        
        self.logo_small_header = None
        self.logo_header_image = None
        self._last_result = None
        self.output = None      
        self.target_entry = None 
        self.progress_bar = None 
        self.loading_label = None 
        self.loading_frame = None
        
        self.history_inner_frame = None
        self.history_window_id = None
        self.image_refs_cache = [] 
        
        if Image and ImageTk:
            try:
                script_dir = Path(sys.argv[0]).resolve().parent
                logo_path = script_dir / "Logo.gif"
                if logo_path.exists():
                    logo_img = Image.open(logo_path)
                    self.iconphoto(True, ImageTk.PhotoImage(logo_img.copy().resize((24, 24), Image.LANCZOS))) 
                    self.logo_header_image = ImageTk.PhotoImage(logo_img.copy().resize((140, 120), Image.LANCZOS))
                    self.logo_small_header = ImageTk.PhotoImage(logo_img.copy().resize((48, 24), Image.LANCZOS))
            except Exception:
                pass

        self._build_login_frame()

    # ... (Login Frame - invariato) ...
    def _build_login_frame(self):
        wrapper_frame = ttk.Frame(self)
        wrapper_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(wrapper_frame, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper_frame, orient="vertical", command=canvas.yview)
        self.login_container = ttk.Frame(canvas, padding="30 20 30 20")
        self.login_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=self.login_container, anchor="nw")
        def _configure_canvas(event): canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event): canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.login_canvas_ref = canvas

        if self.logo_header_image:
            ttk.Label(self.login_container, image=self.logo_header_image).pack(pady=(0, 5))
            ttk.Label(self.login_container, text="CScorza Tools - Instagram OSINT", font=("Arial", 16, "bold"), foreground=ACCENT_COLOR).pack(pady=(0, 20))
        else:
            ttk.Label(self.login_container, text="🕵️ CScorza Tools - Instagram OSINT", font=("Arial", 16, "bold"), foreground=ACCENT_COLOR).pack(pady=(0, 20))

        ttk.Label(self.login_container, text="Phase 1 — Enter your Instagram SessionID", font=("Arial", 12, "bold")).pack(pady=(5, 10))
        ttk.Label(self.login_container, text="❗ Optional: improves access to data.", font=("Arial", 10)).pack(pady=(0, 15))

        ses_frame = ttk.Frame(self.login_container)
        ses_frame.pack(fill="x", pady=5)
        ses_frame.columnconfigure(1, weight=1)
        ttk.Label(ses_frame, text="SessionID:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.session_entry = ttk.Entry(ses_frame, width=30, show="*")
        self.session_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(ses_frame, text="📁 File", command=self._load_session_from_file).grid(row=0, column=2, padx=10)

        ttk.Button(self.login_container, text="➡️ Load and Start Search", 
                   command=lambda: self._on_login_continue(wrapper_frame), cursor="hand2").pack(pady=15, ipadx=10, ipady=5)
        
        ttk.Separator(self.login_container, orient='horizontal').pack(fill='x', pady=15)
        guide_frame = ttk.Frame(self.login_container)
        guide_frame.pack(fill='x', pady=5)
        ttk.Label(guide_frame, text="🚀 Script Guide:", font=("Arial", 11, "bold"), foreground=ACCENT_COLOR).pack(anchor='w', pady=(0, 5))
        guide_content_frame = ttk.Frame(guide_frame)
        guide_content_frame.pack(fill='x')
        guide_items = [("Instagram:", "Retrieve public/obfuscated data."), ("Phone:", "Analyze intl. numbers (+XX...)."), ("Username:", "Cross-check username across socials."), ("SessionID:", "Saved locally in `sessionid.txt`.")]
        for i, (title, desc) in enumerate(guide_items):
            ttk.Label(guide_content_frame, text=f"• {title}", font=("Arial", 10, "bold")).grid(row=i, column=0, sticky='nw')
            ttk.Label(guide_content_frame, text=desc, font=("Arial", 9)).grid(row=i, column=1, sticky='nw', padx=(5, 0))
            guide_content_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(guide_frame, text="🔑 How to retrieve SessionID:", font=("Arial", 11, "bold"), foreground=ACCENT_COLOR).pack(anchor='w', pady=(15, 0))
        ttk.Label(guide_frame, text="1. Log into Instagram on web browser.\n2. F12 > Application > Cookies.\n3. Copy value of 'sessionid'.", font=("Arial", 9)).pack(anchor='w', padx=5)

        ttk.Separator(self.login_container, orient='horizontal').pack(fill='x', pady=15)
        ref_frame = ttk.Frame(self.login_container)
        ref_frame.pack(fill='x')
        ttk.Label(ref_frame, text="© CScorza 2025 | References", font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        ref_data = [("✈️ Telegram:", "https://t.me/CScorzaOSINT"), ("🌐 Web:", "https://cscorza.github.io/CScorza"), ("🐦 Twitter:", "@CScorzaOSINT"), ("📧 Mail:", "cscorzaosint@protonmail.com"), ("₿ BTC:", "bc1qfn9kynt7k26eaxk4tc67q2hjuzhfcmutzq2q6a")]
        ref_grid = ttk.Frame(ref_frame)
        ref_grid.pack(fill='x', padx=5)
        for i, (key, value) in enumerate(ref_data):
            ttk.Label(ref_grid, text=key, font=("Arial", 9, "bold")).grid(row=i, column=0, sticky='w')
            l = ttk.Label(ref_grid, text=value, font=("Arial", 9), foreground=ACCENT_COLOR, cursor="hand2")
            l.grid(row=i, column=1, sticky='w', padx=5)
            l.bind("<Button-1>", lambda e, v=value: self._open_ref_link(v))

    def _open_ref_link(self, val):
        if val.startswith("http"): webbrowser.open_new(val)
        elif val.startswith("@") or val.startswith("bc1"):
            self.clipboard_clear()
            self.clipboard_append(val)
            messagebox.showinfo("Copied", f"Copied: {val}")
        elif val.startswith("cscorzaosint"): webbrowser.open_new(f"mailto:{val}")

    def _load_session_from_file(self):
        try:
            with open("sessionid.txt", "r", encoding="utf-8") as f:
                self.session_entry.delete(0, tk.END)
                self.session_entry.insert(0, f.read().strip())
            messagebox.showinfo("✅ OK", "Loaded.")
        except:
            messagebox.showwarning("⚠️ Warning", "File not found.")

    def _on_login_continue(self, wrapper_widget):
        sessionid = self.session_entry.get().strip()
        if sessionid:
            self.osint.set_sessionid(sessionid)
            try:
                with open("sessionid.txt", "w", encoding="utf-8") as f:
                    f.write(sessionid)
            except: pass
        if hasattr(self, 'login_canvas_ref'): self.login_canvas_ref.unbind_all("<MouseWheel>")
        wrapper_widget.destroy()
        
        self.geometry("")
        
        self._build_search_frame()

    def _open_in_browser(self):
        target = self.target_entry.get().strip()
        if target:
            if target.isdigit(): webbrowser.open("https://instagram.com/explore/people/suggested/")
            else: webbrowser.open(f"https://instagram.com/{target}")
            
    def _open_google_cse(self):
        query = self.target_entry.get().strip()
        if query: webbrowser.open_new(f"https://cse.google.com/cse?cx=d28c23ec014bd4cca#gsc.tab=0&gsc.q={urllib.parse.quote_plus(query)}")

    def _clear_output(self):
        self.target_entry.delete(0, tk.END)
        self.output.delete("1.0", tk.END)
        self._last_result = None
        if self.history_inner_frame:
            for w in self.history_inner_frame.winfo_children(): w.destroy()
        self.image_refs_cache.clear()
        if hasattr(self, 'history_canvas'): self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        messagebox.showinfo("Clear", "Cleaned.")

    # --- 2. SCHERMATA RICERCA ---
    def _build_search_frame(self):
        main_frame = ttk.Frame(self, padding="10 10 10 0")
        main_frame.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        
        if self.logo_small_header:
            ttk.Label(main_frame, text="CScorza - OSINT Instagram", font=("Arial", 18, "bold"), foreground=ACCENT_COLOR, image=self.logo_small_header, compound="left", padding=(0,0,8,0)).pack(pady=(0, 5))
        else:
            ttk.Label(main_frame, text="🔍 CScorza - OSINT Instagram", font=("Arial", 18, "bold"), foreground=ACCENT_COLOR).pack(pady=(0, 5))

        ttk.Label(main_frame, text=f"SessionID Status: {'✅ ACTIVE' if self.osint.sessionid else '❌ NOT ACTIVE'}", font=("Arial", 10, "italic")).pack(pady=(0, 10))

        # INPUT
        input_wrapper = ttk.Frame(main_frame)
        input_wrapper.pack(fill="x", pady=(0, 5)) 
        input_wrapper.columnconfigure(1, weight=1)
        ttk.Label(input_wrapper, text="Target (Username / ID / Phone):", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.target_entry = ttk.Entry(input_wrapper)
        self.target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # --- AREA CARICAMENTO ---
        self.loading_frame = ttk.Frame(main_frame)
        self.loading_frame.pack(fill='x', pady=(5, 5))
        
        self.loading_label = ttk.Label(self.loading_frame, text="We are collecting data for you... / Stiamo raccogliendo i dati per te...", 
                                       font=("Arial", 10, "italic"), foreground="#87CEFA", anchor="center")
        self.progress_bar = ttk.Progressbar(self.loading_frame, mode='indeterminate')

        # BOTTONI
        button_container_outer = ttk.Frame(main_frame)
        button_container_outer.pack(fill="x", pady=(0, 10))
        button_container = ttk.Frame(button_container_outer)
        button_container.pack(fill="x")
        button_container.columnconfigure(0, weight=1) 
        button_container.columnconfigure(1, weight=1) 

        ig_wrapper = ttk.Frame(button_container)
        ig_wrapper.grid(row=0, column=0, sticky="n", padx=(0, 10)) 
        ttk.Label(ig_wrapper, text="OSINT Instagram", font=("Arial", 10, "bold"), foreground=ACCENT_COLOR).pack(pady=(0, 3))
        ig_btns = ttk.Frame(ig_wrapper)
        ig_btns.pack(pady=(0, 5))
        ttk.Button(ig_btns, text="User Info", command=self._on_user_info_threaded, cursor="hand2").pack(side="left", padx=5)
        ttk.Button(ig_btns, text="ID Info", command=self._on_id_info_threaded, cursor="hand2").pack(side="left", padx=5)
        ttk.Button(ig_wrapper, text="🌐 Explore Profile", command=self._open_in_browser, cursor="hand2").pack()
        
        global_wrapper = ttk.Frame(button_container)
        global_wrapper.grid(row=0, column=1, sticky="n", padx=(10, 0))
        ttk.Label(global_wrapper, text="Global Search:", font=("Arial", 10, "bold"), foreground=ACCENT_COLOR).pack(pady=(0, 3))
        gl_btns = ttk.Frame(global_wrapper)
        gl_btns.pack(pady=(0, 5)) 
        ttk.Button(gl_btns, text="📞 Phone Search", command=self._on_phone_info_threaded, cursor="hand2").pack(side="left", padx=5)
        ttk.Button(gl_btns, text="🌐 Username Search", command=self._on_global_search_threaded, cursor="hand2").pack(side="left", padx=5)
        ttk.Button(global_wrapper, text="🔥 Advanced Dorks", command=self._open_dorks_window, cursor="hand2").pack(pady=(5,0)) 

        # RISULTATI
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill="both", expand=True, pady=(5, 12))
        
        result_frame.columnconfigure(0, weight=0, minsize=240) 
        result_frame.columnconfigure(1, weight=1)
        result_frame.rowconfigure(0, weight=1)

        history_container = ttk.LabelFrame(result_frame, text=" Profiles History (Right Click for Options) ", padding=5)
        history_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # CANVAS CONFIGURATO PER ESPANDERSI
        self.history_canvas = tk.Canvas(history_container, width=220, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_canvas.yview)
        
        self.history_inner_frame = ttk.Frame(self.history_canvas)
        
        # --- FIX: Questo bind fa espandere la window interna alla larghezza del canvas ---
        self.history_window_id = self.history_canvas.create_window((0, 0), window=self.history_inner_frame, anchor="nw")
        
        def _configure_history_canvas(event):
            self.history_canvas.itemconfig(self.history_window_id, width=event.width)
        
        self.history_canvas.bind("<Configure>", _configure_history_canvas)
        # --------------------------------------------------------------------------------
        
        self.history_inner_frame.bind("<Configure>", lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.history_canvas.bind_all("<MouseWheel>", lambda e: self.history_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.output = scrolledtext.ScrolledText(result_frame, width=70, height=30, font=("Consolas", 10), bg='#1c1c1c', fg='lightgrey', insertbackground='white')
        self.output.grid(row=0, column=1, sticky="nsew")
        self.output.tag_config('highlight', foreground='#ADD8E6')
        self.output.tag_config('error', foreground='#FA8072')
        self.output.tag_config('obfuscated', foreground='#FFD700')
        self.output.tag_config('link', foreground='#00BFFF', underline=1)
        self.output.tag_config('time', foreground='#98fb98')

        ops_frame = ttk.Frame(main_frame, padding="0 0 0 5")
        ops_frame.pack(fill="x")
        ttk.Button(ops_frame, text="🗑️ Clear All", command=self._clear_output, cursor="hand2").pack(side="right") 
        ttk.Button(ops_frame, text="💾 Save to File", command=self._save_last_result, cursor="hand2").pack(side="right", padx=10)

    # --- HELPERS THREADING ---
    def _start_loading(self):
        self.loading_label.pack(fill='x', pady=(0, 5))
        self.progress_bar.pack(fill='x')
        self.progress_bar.start(10)

    def _stop_loading(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.loading_label.pack_forget()

    def _run_in_thread(self, task_func, callback_func):
        self._start_loading()
        def wrapper():
            try:
                result = task_func()
                self.after(0, lambda: callback_func(result))
            except Exception as e:
                print(e)
            finally:
                self.after(0, self._stop_loading)
        
        threading.Thread(target=wrapper, daemon=True).start()

    # --- GOOGLE DORKS WINDOW (MULTI-ENGINE & REGION) ---
    def _open_dorks_window(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter a target (username/name) in the input box first.")
            return

        top = tk.Toplevel(self)
        top.title("Advanced Intelligence Dorks")
        
        # CONFIGURAZIONE SFONDO POPUP
        top.configure(bg=BG_COLOR)
        
        top.minsize(500, 600)
        
        ttk.Label(top, text=f"Target: {target}", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Engine Frame
        eng_frame = ttk.LabelFrame(top, text=" Select Search Engine ", padding=10)
        eng_frame.pack(fill="x", padx=10, pady=5)
        
        engine_var = tk.StringVar(value="Google")
        
        # Region Selection for DDG
        region_frame = ttk.Frame(top) # Frame standard, eredita bg
        
        ddg_regions = {
            "🌍 Global": "", "🇮🇹 Italy": "it-it", "🇺🇸 USA": "us-en", "🇬🇧 UK": "uk-en",
            "🇫🇷 France": "fr-fr", "🇩🇪 Germany": "de-de", "🇪🇸 Spain": "es-es", "🇷🇺 Russia": "ru-ru",
            "🇨🇳 China": "cn-zh", "🇯🇵 Japan": "jp-jp", "🇧🇷 Brazil": "br-pt", "🇳🇱 Netherlands": "nl-nl"
        }
        
        ddg_region_var = tk.StringVar(value="🌍 Global")
        ttk.Label(region_frame, text="DuckDuckGo Region:").pack(side="left", padx=(10, 5))
        region_cb = ttk.Combobox(region_frame, textvariable=ddg_region_var, values=list(ddg_regions.keys()), state="readonly")
        region_cb.pack(side="left")

        # Scrollable Area
        dorks_canvas = tk.Canvas(top, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=dorks_canvas.yview)
        dorks_inner = ttk.Frame(dorks_canvas)
        
        dorks_inner.bind("<Configure>", lambda e: dorks_canvas.configure(scrollregion=dorks_canvas.bbox("all")))
        dorks_canvas.create_window((0, 0), window=dorks_inner, anchor="nw", width=510)
        dorks_canvas.configure(yscrollcommand=scrollbar.set)
        
        dorks_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        def update_dorks(*args):
            if engine_var.get() == "DuckDuckGo":
                region_frame.pack(fill="x", pady=5)
            else:
                region_frame.pack_forget()

            for w in dorks_inner.winfo_children(): w.destroy()
            
            eng = engine_var.get()
            base_url = ""
            dork_list = []

            if eng == "Google":
                base_url = "https://www.google.com/search?q={}"
                dork_list = [
                    ("Social Media (Broad)", f'site:facebook.com OR site:twitter.com OR site:instagram.com OR site:tiktok.com OR site:reddit.com "{target}"'),
                    ("Telegram Channels", f'site:t.me OR site:telegram.me "{target}"'),
                    ("WhatsApp Links", f'site:chat.whatsapp.com OR site:wa.me "{target}"'),
                    ("Confidential Files", f'filetype:txt OR filetype:pdf OR filetype:xls OR filetype:doc "{target}"'),
                    ("Pastebin & Leaks", f'site:pastebin.com OR site:justpaste.it OR site:github.com "{target}"'),
                    ("LinkedIn Profiles", f'site:linkedin.com "{target}"'),
                    ("Passwords (Risky)", f'"{target}" "password"'),
                    ("Email Variations", f'"{target}@gmail.com" OR "{target}@yahoo.com"')
                ]
            elif eng == "DuckDuckGo":
                kl_code = ddg_regions.get(ddg_region_var.get(), "")
                base_url = "https://duckduckgo.com/?q={}"
                if kl_code: base_url += f"&kl={kl_code}"
                
                dork_list = [
                    ("Social Media", f'site:facebook.com OR site:twitter.com OR site:instagram.com "{target}"'),
                    ("Telegram/WhatsApp", f'site:t.me OR site:wa.me "{target}"'),
                    ("PDF/Docs", f'filetype:pdf OR filetype:doc "{target}"'),
                    ("Deep Web (Onion)", f'"{target}" site:.onion'),
                    ("Pastebin Search", f'site:pastebin.com "{target}"'),
                    ("Exact Match", f'"{target}"'),
                ]
            elif eng == "Yandex":
                base_url = "https://yandex.com/search/?text={}"
                dork_list = [
                    ("VKontakte (Russia)", f'site:vk.com "{target}"'),
                    ("Telegram (Ru)", f'site:t.me "{target}"'),
                    ("WhatsApp Mentions", f'"WhatsApp" "{target}"'),
                    ("Documents (Mime)", f'mime:pdf OR mime:doc "{target}"'),
                    ("Eastern Europe Profiles", f'site:ok.ru OR site:mail.ru "{target}"'),
                    ("Images/Faces", f'mime:jpg OR mime:png "{target}"')
                ]

            for label, query in dork_list:
                btn = ttk.Button(dorks_inner, text=label, 
                                 command=lambda q=query, u=base_url: webbrowser.open(u.format(urllib.parse.quote_plus(q))))
                btn.pack(fill="x", pady=2)

        ttk.Radiobutton(eng_frame, text="🇬 Google", variable=engine_var, value="Google", command=update_dorks).pack(side="left", padx=10)
        ttk.Radiobutton(eng_frame, text="🦆 DuckDuckGo", variable=engine_var, value="DuckDuckGo", command=update_dorks).pack(side="left", padx=10)
        ttk.Radiobutton(eng_frame, text="🇷🇺 Yandex", variable=engine_var, value="Yandex", command=update_dorks).pack(side="left", padx=10)
        
        region_cb.bind("<<ComboboxSelected>>", update_dorks)
        
        update_dorks()

    # --- CONTEXT MENU FOR IMAGES ---
    def _show_context_menu(self, event, img_data, img_url):
        menu = Menu(self, tearoff=0)
        
        def save_img():
            f = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
            if f:
                with open(f, "wb") as file: file.write(img_data)
                messagebox.showinfo("Saved", "Image saved.")
        
        def google_lens():
            if img_url and "http" in img_url:
                webbrowser.open(f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(img_url)}")
            else:
                messagebox.showinfo("Info", "Direct URL unavailable for upload. Try saving and dragging to Google Images.")

        def yandex_img():
            if img_url and "http" in img_url:
                webbrowser.open(f"https://yandex.com/images/search?rpt=imageview&url={urllib.parse.quote_plus(img_url)}")
            else:
                messagebox.showinfo("Info", "Direct URL unavailable.")

        menu.add_command(label="💾 Save Image As...", command=save_img)
        menu.add_separator()
        menu.add_command(label="🔍 Search on Google Lens", command=google_lens)
        menu.add_command(label="🇷🇺 Search on Yandex Images", command=yandex_img)
        
        if img_url:
            menu.add_separator()
            menu.add_command(label="🔗 Copy Image URL", command=lambda: self.clipboard_append(img_url))

        menu.tk_popup(event.x_root, event.y_root)

    # --- WRAPPERS ---
    def _on_user_info_threaded(self):
        u = self.target_entry.get().strip()
        if not u: return
        self._run_in_thread(lambda: self.osint.profile_by_username(u), lambda res: self._post_process_ig_result(u, res))

    def _on_id_info_threaded(self):
        v = self.target_entry.get().strip()
        if not v.isdigit(): return
        self._run_in_thread(lambda: self.osint.profile_by_id(v), lambda res: self._post_process_ig_result(v, res))

    def _post_process_ig_result(self, query, info):
        self._last_result = (query, info)
        self._display_result(info)

    def _on_phone_info_threaded(self):
        p = self.target_entry.get().strip()
        if not p or not p.startswith('+'): return
        self._run_in_thread(lambda: phone_info_osint(p), lambda res: self._display_phone_result(p, res))

    def _display_phone_result(self, p, info):
        ts = self._get_timestamp()
        self.output.insert(tk.END, f"\n[{ts}] 📞 Phone Analysis: {p}\n{'='*40}\n", 'time')
        if "Error" in info: self.output.insert(tk.END, f"{info['Error']}\n", 'error')
        else:
            for k, v in info.items(): self.output.insert(tk.END, f"{k}: {v}\n", 'link' if 'Link' in k else 'highlight')
        self.output.see(tk.END)
        self.output.tag_bind('link', '<Button-1>', self._click_link)

    def _on_global_search_threaded(self):
        u = self.target_entry.get().strip()
        if not u: return
        self._run_in_thread(lambda: username_info_global(u), lambda res: self._display_global_result(u, res))

    def _display_global_result(self, u, res):
        ts = self._get_timestamp()
        self.output.insert(tk.END, f"\n[{ts}] 🌍 Global Search: {u}\n{'='*40}\n", 'time')
        for s, i in res.items():
            self.output.insert(tk.END, f"{i['icon']} {s}: ")
            if i['status'] == "Found": 
                self.output.insert(tk.END, i['url']+"\n", 'link')
                if i.get("image_url"):
                    img_data = download_image_to_bytes(i["image_url"])
                    if img_data: self._add_history_card(f"{s}: {u}", img_data, i['url'])
            else: 
                self.output.insert(tk.END, i['status']+"\n", 'error' if 'Not' in i['status'] else '')
        self.output.see(tk.END)
        self.output.tag_bind('link', '<Button-1>', self._click_link)

    def _get_timestamp(self):
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    def _add_history_card(self, title, image_bytes, url_to_open=None):
        card_frame = ttk.Frame(self.history_inner_frame, relief="ridge", borderwidth=2)
        # fill='x' è cruciale qui
        card_frame.pack(side="top", pady=(0, 10), padx=5, fill="x")

        if Image and ImageTk and image_bytes:
            try:
                img = Image.open(BytesIO(image_bytes))
                img.thumbnail((160, 160))
                photo_tk = ImageTk.PhotoImage(img)
                self.image_refs_cache.append(photo_tk)
                img_lbl = ttk.Label(card_frame, image=photo_tk, cursor="hand2")
                img_lbl.pack(pady=5)
                
                if url_to_open: img_lbl.bind("<Button-1>", lambda e, u=url_to_open: webbrowser.open(u))
                
                # Context Menu Bind
                img_lbl.bind("<Button-3>", lambda e: self._show_context_menu(e, image_bytes, url_to_open))
            except:
                ttk.Label(card_frame, text="[Img Error]").pack(pady=10)
        else:
            ttk.Label(card_frame, text="[No Image]", font=("Arial", 9)).pack(pady=15)

        ttk.Label(card_frame, text=title, font=("Arial", 9, "bold"), anchor="center", foreground="#87CEFA", wraplength=200).pack(fill="x", pady=(0, 5))
        self.history_inner_frame.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _display_result(self, info: dict):
        display_name = info.get("Username") or info.get("Full Name") or "Unknown"
        profile_url = info.get("Profile Pic URL")
        self._add_history_card(display_name, info.get("Profile Picture Data"), profile_url)

        ts = self._get_timestamp()
        self.output.insert(tk.END, "\n" + "="*40 + "\n")
        self.output.insert(tk.END, f"[{ts}] Search Executed\n", 'time')
        
        if "Error" in info:
            self.output.insert(tk.END, f"❌ Error: {info.get('Error')}\n", 'error')
        else:
            self.output.insert(tk.END, f"✅ Result Found for {display_name}:\n")
            keys = ["Username", "ID", "Full Name", "Biography", "Followers", "Following", "Posts", "Private", "Verified", "Public Email", "Public Phone", "Obfuscated Email", "Obfuscated Phone"]
            for k in keys:
                if k in info:
                    tag = 'highlight'
                    if "Obfuscated" in k or "Public" in k: tag = 'obfuscated'
                    self.output.insert(tk.END, f"{k}: ", tag)
                    self.output.insert(tk.END, f"{info[k]}\n")
            for k, v in info.items():
                if k not in keys and k not in ["Profile Picture Data", "Profile Pic URL", "Media", "PK"]:
                    self.output.insert(tk.END, f"{k}: {v}\n")
        self.output.insert(tk.END, "="*40 + "\n\n")
        self.output.see(tk.END)

    def _click_link(self, event):
        try:
            idx = self.output.index(f"@{event.x},{event.y}")
            ranges = self.output.tag_ranges('link')
            for s, e in zip(ranges[0::2], ranges[1::2]):
                if self.output.compare(s, '<=', idx) and self.output.compare(idx, '<', e):
                    webbrowser.open(self.output.get(s, e).strip().split(": ")[-1])
        except: pass

    def _save_last_result(self):
        if not self._last_result:
            messagebox.showinfo("Info", "No results to save.")
            return
        name, data = self._last_result
        ftypes = [("JSON File", "*.json"), ("CSV File", "*.csv"), ("Word/Text File", "*.doc"), ("All Files", "*.*")]
        f = filedialog.asksaveasfilename(initialfile=f"{name}_osint", filetypes=ftypes, defaultextension=".json")
        if not f: return
        clean_data = {k: v for k, v in data.items() if k != "Profile Picture Data"}
        ext = os.path.splitext(f)[1].lower()
        try:
            if ext == ".json":
                with open(f, "w", encoding="utf-8") as fp: json.dump(clean_data, fp, indent=4)
            elif ext == ".csv":
                with open(f, "w", newline="", encoding="utf-8") as fp:
                    w = csv.writer(fp)
                    w.writerow(["Key", "Value"])
                    for k, v in clean_data.items(): w.writerow([k, str(v)])
            elif ext == ".doc" or ext == ".txt":
                with open(f, "w", encoding="utf-8") as fp:
                    fp.write(f"REPORT: {name}\nDATE: {datetime.now()}\n\n")
                    for k, v in clean_data.items(): fp.write(f"{k}: {v}\n")
            save_result_files_img_only(name, data, f.rsplit('.', 1)[0])
            messagebox.showinfo("Saved", f"Saved to {f}")
        except Exception as e: messagebox.showerror("Error", str(e))

def main():
    app = CScorzaOSINTApp()
    app.mainloop()

if __name__ == "__main__":
    main()
