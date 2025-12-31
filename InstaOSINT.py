#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CScorza InstaOSINT Pro V2.0 - OS Intelligence Pro
Developed by: CScorza OSINT Specialist
Version: 2.0 (2025 Blue Web, Grid Layout & Clickable Links)
"""

import os, sys, subprocess, threading, webbrowser, time, base64, json, hmac, hashlib, uuid, re, asyncio, io
from pathlib import Path
from tempfile import NamedTemporaryFile

# --- AUTO-SETUP ---
def setup_env():
    script_path = Path(__file__).resolve()
    venv_path = script_path.parent / "venv_cscorza_v4"
    py = venv_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    pip = venv_path / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
    
    if sys.prefix != str(venv_path):
        if not venv_path.exists():
            print("[*] Inizializzazione Quantum Suite V2.0...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("[*] Sincronizzazione dipendenze professionali...")
            subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(pip), "install", "flask", "requests", "phonenumbers", "telethon", "fpdf2", "python-docx", "pandas", "openpyxl"], check=True)
        os.execv(str(py), [str(py), str(script_path)])

if __name__ == "__main__" and "FLASK_RUN_FROM_CLI" not in os.environ:
    setup_env()

# --- IMPORTAZIONI ---
from flask import Flask, render_template_string, request, jsonify, send_file
import requests, phonenumbers, pandas as pd
from phonenumbers import carrier, geocoder
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from fpdf import FPDF
from docx import Document
from docx.shared import Inches

app = Flask(__name__)
session = requests.Session()

# --- CONFIGURAZIONE ---
CREDS_FILE = "credenziali API.json"
IG_KEY = "e6358aeede676184b9fe702b30f4fd35e71744605e39d2181a34cede076b3c33"
BASE_API = "https://i.instagram.com/api/v1"
LOGO_URL = "https://github.com/CScorza.png"
APP_ID_WEBPROFILE = "936619743392459"
APP_ID_LOOKUP = "124024574287414"

SOCIAL_MAP = {
    "Instagram": {"base": "instagram.com/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174855.png"},
    "Facebook": {"base": "facebook.com/", "icon": "https://cdn-icons-png.flaticon.com/512/124/124010.png"},
    "Twitter/X": {"base": "x.com/", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968830.png"},
    "TikTok": {"base": "tiktok.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/3046/3046121.png"},
    "LinkedIn": {"base": "linkedin.com/in/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174857.png"},
    "GitHub": {"base": "github.com/", "icon": "https://cdn-icons-png.flaticon.com/512/25/25231.png"},
    "YouTube": {"base": "youtube.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/1384/1384060.png"},
    "Pinterest": {"base": "pinterest.com/", "icon": "https://cdn-icons-png.flaticon.com/512/145/145808.png"},
    "Reddit": {"base": "reddit.com/user/", "icon": "https://cdn-icons-png.flaticon.com/512/3536/3536761.png"},
    "Twitch": {"base": "twitch.tv/", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968819.png"},
    "Discord": {"base": "discord.com/users/", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968756.png"},
    "WhatsApp": {"base": "wa.me/", "icon": "https://cdn-icons-png.flaticon.com/512/733/733585.png"},
    "Telegram": {"base": "t.me/", "icon": "https://cdn-icons-png.flaticon.com/512/2111/2111646.png"},
    "Threads": {"base": "threads.net/@", "icon": "https://cdn-icons-png.flaticon.com/512/10091/10091234.png"},
    "Medium": {"base": "medium.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968906.png"},
    "Snapchat": {"base": "snapchat.com/add/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174870.png"},
    "Behance": {"base": "behance.net/", "icon": "https://cdn-icons-png.flaticon.com/512/733/733541.png"},
    "Dribbble": {"base": "dribbble.com/", "icon": "https://cdn-icons-png.flaticon.com/512/733/733544.png"},
    "Stack Overflow": {"base": "stackoverflow.com/users/", "icon": "https://cdn-icons-png.flaticon.com/512/2111/2111628.png"},
    "SoundCloud": {"base": "soundcloud.com/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174871.png"},
    "Spotify": {"base": "open.spotify.com/user/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174872.png"},
    "DeviantArt": {"base": "deviantart.com/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174842.png"},
    "Patreon": {"base": "patreon.com/", "icon": "https://cdn-icons-png.flaticon.com/512/2111/2111545.png"},
    "Mastodon": {"base": "mastodon.social/@", "icon": "https://cdn-icons-png.flaticon.com/512/2525/2525032.png"},
    "Quora": {"base": "quora.com/profile/", "icon": "https://cdn-icons-png.flaticon.com/512/3536/3536648.png"},
    "Slack": {"base": "slack.com/", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968929.png"},
    "Steam": {"base": "steamcommunity.com/id/", "icon": "https://cdn-icons-png.flaticon.com/512/733/733575.png"},
    "Vimeo": {"base": "vimeo.com/", "icon": "https://cdn-icons-png.flaticon.com/512/174/174875.png"},
    "Skype": {"base": "skype:", "icon": "https://cdn-icons-png.flaticon.com/512/174/174869.png"},
    "WeChat": {"base": "wechat.com/", "icon": "https://cdn-icons-png.flaticon.com/512/3670/3670311.png"},
    "VK": {"base": "vk.com/", "icon": "https://cdn-icons-png.flaticon.com/512/145/145813.png"},
    "OpenSea": {"base": "opensea.io/", "icon": "https://cdn-icons-png.flaticon.com/512/6124/6124991.png"},
    "ArtStation": {"base": "artstation.com/", "icon": "https://cdn-icons-png.flaticon.com/512/3670/3670189.png"},
    "Product Hunt": {"base": "producthunt.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/2111/2111559.png"},
    "Hugging Face": {"base": "huggingface.co/", "icon": "https://cdn-icons-png.flaticon.com/512/11516/11516240.png"},
    "GitLab": {"base": "gitlab.com/", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968853.png"},
    "Bluesky": {"base": "bsky.app/profile/", "icon": "https://cdn-icons-png.flaticon.com/512/11104/11104255.png"},
    "Goodreads": {"base": "goodreads.com/", "icon": "https://cdn-icons-png.flaticon.com/512/3670/3670175.png"},
    "Letterboxd": {"base": "letterboxd.com/", "icon": "https://cdn-icons-png.flaticon.com/512/10091/10091216.png"},
    "Kaggle": {"base": "kaggle.com/", "icon": "https://cdn-icons-png.flaticon.com/512/3670/3670178.png"},
    "Etsy": {"base": "etsy.com/shop/", "icon": "https://cdn-icons-png.flaticon.com/512/825/825513.png"},
    "TripAdvisor": {"base": "tripadvisor.com/Profile/", "icon": "https://cdn-icons-png.flaticon.com/512/2111/2111664.png"},
    "Figma": {"base": "figma.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/5968/5968705.png"},
    "Unsplash": {"base": "unsplash.com/@", "icon": "https://cdn-icons-png.flaticon.com/512/1051/1051332.png"},
    "Buy Me a Coffee": {"base": "buymeacoffee.com/", "icon": "https://cdn-icons-png.flaticon.com/512/5753/5753177.png"}
}

class OSINTCore:
    def __init__(self):
        self.creds = {"sid": "", "tg_id": "", "tg_hash": ""}
        if os.path.exists(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r") as f: self.creds = json.load(f)
            except: pass

    def save_creds(self, d):
        self.creds.update(d); Path(CREDS_FILE).write_text(json.dumps(self.creds, indent=4))

    def instagram_lookup(self, username):
        guid = str(uuid.uuid4()); device_id = f"android-{uuid.uuid4().hex[:16]}"
        payload = {"q": username, "device_id": device_id, "guid": guid, "_csrftoken": "missing"}
        json_p = json.dumps(payload, separators=(',', ':'))
        signed = hmac.new(IG_KEY.encode(), json_p.encode(), hashlib.sha256).hexdigest() + "." + json_p
        headers = {"X-IG-App-ID": APP_ID_LOOKUP, "User-Agent": "Instagram 292.0.0.17.111 Android", "Content-Type": "application/x-www-form-urlencoded"}
        try:
            cookies = {"sessionid": self.creds['sid']} if self.creds['sid'] else {}
            r = session.post(f"{BASE_API}/users/lookup/", headers=headers, data={"signed_body": signed, "ig_sig_key_version": "4"}, cookies=cookies, timeout=10, allow_redirects=False)
            res = r.json(); u = res.get("user", {})
            return {"Email Obf": u.get("obfuscated_email") or res.get("obfuscated_email") or "N/A", "Phone Obf": u.get("obfuscated_phone") or res.get("obfuscated_phone") or "N/A"}
        except: return {"Email Obf": "N/A", "Phone Obf": "N/A"}

core = OSINTCore()

# --- UI HTML ---
HTML_UI = r"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>CScorza InstaOSINT Pro V2.0</title>
    <style>
        :root { --bg: #0a0a0a; --panel: #141414; --accent: #6495ED; --gold: #FFD700; --text: #d0d0d0; --wa-green: #25D366; --tg-blue: #0088cc; }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        #login-view { position: fixed; inset: 0; background: var(--bg); display: flex; justify-content: center; align-items: center; z-index: 2000; overflow-y: auto; padding: 40px 0; }
        .setup-card { background: var(--panel); padding: 35px; border-radius: 20px; border: 1px solid #222; width: 900px; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        
        .cred-box { display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin: 25px 0; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px; }
        .cred-item { text-decoration: none; color: var(--text); font-size: 11px; display: flex; flex-direction: column; align-items: center; gap: 5px; transition: 0.3s; width: 85px; }
        .cred-item:hover { color: var(--accent); transform: translateY(-3px); }
        .cred-item img { width: 28px; height: 28px; object-fit: contain; }
        
        .crypto-box { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: left; margin-top: 20px; }
        .crypto-card { background: #000; padding: 12px; border-radius: 8px; border-left: 3px solid var(--gold); }
        .crypto-card label { display: block; font-size: 10px; color: var(--gold); font-weight: bold; margin-bottom: 5px; }
        .crypto-card code { font-size: 10px; color: #aaa; word-break: break-all; font-family: monospace; }

        #dashboard { display: none; flex: 1; width: 100%; height: 100%; }
        #sidebar { width: 340px; background: #050505; border-right: 1px solid #222; padding: 20px; display: flex; flex-direction: column; }
        #main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #0a0a0a; }
        .header-brand { padding: 15px 25px; background: #000; border-bottom: 1px solid #222; display: flex; align-items: center; gap: 15px; }
        .header-brand img { width: 45px; height: 45px; border-radius: 50%; border: 2px solid var(--accent); }
        .header-brand h2 { color: var(--accent); margin: 0; letter-spacing: 2px; font-size: 24px; text-transform: uppercase; font-weight: 800; }
        
        .unified-header { padding: 20px; background: #0a0a0a; }
        .unified-bar { display: grid; grid-template-columns: 2.2fr 0.9fr 0.9fr 1fr; gap: 12px; align-items: center; width: 100%; }
        .unified-input { background: #000; border: 1px solid #333; color: #fff; padding: 14px; border-radius: 8px; font-size: 16px; outline: none; transition: 0.3s; }
        .unified-input:focus { border-color: var(--accent); box-shadow: 0 0 10px rgba(100,149,237,0.2); }
        
        .dork-bar { grid-column: span 4; display: grid; grid-template-columns: 1fr 1fr 2fr 1.5fr; gap: 10px; margin-top: 10px; padding-top: 10px; }
        #progress-container { width: 100%; height: 4px; background: #222; display: none; overflow: hidden; }
        #progress-bar { width: 30%; height: 100%; background: var(--accent); animation: loading 1.2s infinite ease-in-out; }
        @keyframes loading { from { transform: translateX(-100%); } to { transform: translateX(400%); } }

        .results-area { flex: 1; overflow-y: auto; padding: 0 20px 20px 20px; }
        
        /* SCACCHIERA GRID SYSTEM */
        #results-container { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); 
            gap: 25px; 
            width: 100%; 
        }
        
        .res-card { background: #111; border: 1px solid #222; border-radius: 12px; position: relative; transition: 0.3s; animation: slideUp 0.3s ease; height: fit-content; overflow: hidden; }
        .card-top { padding: 18px; display: flex; align-items: center; gap: 18px; cursor: pointer; background: #181818; }
        .card-top:hover { background: #222; }
        
        .profile-img-container { position: relative; width: 80px; height: 80px; flex-shrink: 0; }
        .profile-img-container img.main-pfp { width: 100%; height: 100%; border-radius: 50%; border: 2px solid var(--accent); object-fit: cover; background: #222; }
        .social-mini-icon { position: absolute; bottom: 0; right: 0; width: 28px; height: 28px; border-radius: 50%; background: #fff; border: 2px solid #000; }
        
        /* ESPANSIONE DETTAGLI */
        .card-body { padding: 20px; display: none; grid-template-columns: 1fr; gap: 14px; font-size: 14px; border-top: 1px solid #222; background: #0d0d0d; }
        .res-card.open .card-body { display: grid; }
        
        .data-box { background: #080808; padding: 14px; border-radius: 8px; border-bottom: 1px solid #222; word-break: break-all; }
        .data-box label { display: block; font-size: 11px; color: var(--accent); font-weight: bold; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1.2px; }
        .data-box span { color: #fff; line-height: 1.8; }
        
        /* ELENCO DEI LINK */
        .data-box span a { 
            display: block; 
            color: var(--accent); 
            text-decoration: none; 
            padding: 5px 0;
            border-bottom: 1px solid rgba(100, 149, 237, 0.1);
            font-size: 15px;
        }
        .data-box span a:last-child { border-bottom: none; }
        .data-box span a:before { content: "• "; color: var(--gold); font-weight: bold; }
        .data-box span a:hover { color: #fff; background: rgba(255,255,255,0.05); }

        .data-box.gold span { color: var(--gold); font-weight: bold; }

        .btn { background: var(--accent); color: white; border: none; padding: 14px 22px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        .btn-ig { background: linear-gradient(45deg, #f09433, #bc1888); }
        .btn-global { background: linear-gradient(45deg, #2c3e50, #000000); border: 1px solid #333; }
        
        #ctx-menu { position: fixed; display: none; background: #1a1a1a; border: 1px solid #444; border-radius: 8px; z-index: 5000; min-width: 220px; box-shadow: 0 10px 40px #000; }
        .ctx-item { padding: 12px 18px; cursor: pointer; font-size: 14px; border-bottom: 1px solid #222; }
        .ctx-item:hover { background: var(--accent); color: #fff; }

        .hist-card { background: #1a1a1a; padding: 12px; border-radius: 8px; margin-bottom: 12px; cursor: pointer; border: 1px solid transparent; }
        .hist-card:hover { border-color: var(--accent); }

        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; } }
    </style>
</head>
<body>

    <div id="login-view">
        <div class="setup-card">
            <img src="{{logo_url}}" style="width:110px; border-radius:50%; border:3px solid var(--accent); margin-bottom:15px;">
            <h1 style="color:var(--accent); margin:0; letter-spacing: 5px;">CScorza InstaOSINT Pro</h1>
            <p style="opacity:0.5; margin-bottom: 30px;">Open Source Intelligence</p>
            
            <div class="cred-box">
                <a href="https://github.com/CScorza" target="_blank" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/25/25231.png"> GitHub</a>
                <a href="https://twitter.com/CScorzaOSINT" target="_blank" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/3256/3256013.png"> X (Twitter)</a>
                <a href="https://bsky.app/profile/cscorza.bsky.social" target="_blank" class="cred-item"><img src="https://img.icons8.com/color/48/butterfly.png"> BlueSky</a>
                <a href="https://t.me/CScorzaOSINT" target="_blank" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png"> Telegram</a>
                <a href="https://www.linkedin.com/in/cscorza" target="_blank" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png"> LinkedIn</a>
                <a href="https://cscorza.github.io/CScorza/" target="_blank" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/12384/12384156.png"> Web Site</a>
                <a href="mailto:cscorzaosint@protonmail.com" class="cred-item"><img src="https://cdn-icons-png.flaticon.com/512/732/732200.png"> Email</a>
            </div>

            <div style="text-align:left; display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-bottom: 25px;">
                <div style="grid-column: span 2;">
                    <label style="font-size:10px; color:var(--accent)">INSTAGRAM SESSIONID</label>
                    <input type="password" id="sid-input" style="width:97%; background:#000; border:1px solid #333; color:#fff; padding:10px;" value="{{creds.sid}}">
                </div>
                <div><label style="font-size:10px; color:var(--accent)">TELEGRAM API ID</label><input type="text" id="tg-id" style="width:90%; background:#000; border:1px solid #333; color:#fff; padding:10px;" value="{{creds.tg_id}}"></div>
                <div><label style="font-size:10px; color:var(--accent)">TELEGRAM API HASH</label><input type="password" id="tg-hash" style="width:90%; background:#000; border:1px solid #333; color:#fff; padding:10px;" value="{{creds.tg_hash}}"></div>
            </div>

            <div style="display:flex; gap:10px; margin-bottom: 30px;">
                <button class="btn" onclick="startApp()" style="flex:2; padding:18px; font-size:13px; letter-spacing: 2px;">AUTHORIZE & LAUNCH SYSTEM</button>
                <div style="flex:1;"><label class="btn" style="display:block; background:#333; text-align:center; padding:18px; cursor: pointer;">📂 LOAD JSON <input type="file" id="json-file" hidden accept=".json" onchange="loadCredsFile(this)"></label></div>
            </div>

            <p style="font-size: 11px; color: var(--accent); font-weight: bold; margin-bottom: 15px;">☕ Supporta il Progetto / Support the Project</p>
            <div class="crypto-box">
                <div class="crypto-card"><label>BITCOIN (BTC)</label><code>bc1qfn9kynt7k26eaxk4tc67q2hjuzhfcmutzq2q6a</code></div>
                <div class="crypto-card"><label>TON (Telegram Open Network)</label><code>UQBtLB6m-7q8j9Y81FeccBEjccvl34Ag5tWaUD</code></div>
            </div>
            <p style="margin-top: 30px; font-size: 10px; opacity: 0.5;">© 2025 CScorza Investigation</p>
        </div>
    </div>

    <div id="dashboard">
        <div id="sidebar">
            <h4 style="text-align:center; color:var(--accent); letter-spacing:2px; font-size:12px;">CRONOLOGIA TARGET</h4>
            <div id="hist-list" style="flex:1; overflow-y:auto;"></div>
            <div style="border-top:1px solid #222; padding-top:15px;">
                <select id="export-format" style="width:100%; margin-bottom:10px; background:#000; color:white; border:1px solid #333; padding:8px;">
                    <option value="pdf">PDF Report Intelligence</option>
                    <option value="excel">Excel Data Matrix</option>
                </select>
                <button class="btn" onclick="buildReport()" style="width:100%; background:#2e7d32; margin-bottom:5px;">📋 GENERA REPORT </button>
                <button class="btn" onclick="location.reload()" style="width:100%; background:#800;">🗑️ RESET</button>
            </div>
        </div>

        <div id="main-content">
            <div class="header-brand"><img src="{{logo_url}}"><h2>CScorza InstaOSINT Pro</h2></div>
            <div class="unified-header">
                <div class="unified-bar">
                    <input type="text" id="main-search" class="unified-input" placeholder="User, Phone (+39...) o Target Dork...">
                    <button class="btn btn-ig" onclick="runSearch('ig')">INSTAGRAM</button>
                    <button class="btn" onclick="runSearch('phone')">📞 PHONE</button>
                    <button class="btn btn-global" onclick="runSearch('global')">🌐 SOCIAL SCANNER</button>
                    <div class="dork-bar">
                        <select id="dork-engine" onchange="toggleDorkUI()" style="background:#000; color:white; border:1px solid #333; padding:10px;"><option value="google">Google</option><option value="duckduckgo">DuckDuckGo</option><option value="bing">Bing</option></select>
                        <select id="dork-country" disabled style="background:#000; color:white; border:1px solid #333; padding:10px;">
                            <optgroup label="Europa"><option value="it-it">Italia</option><option value="uk-en">Regno Unito</option><option value="de-de">Germania</option><option value="fr-fr">Francia</option><option value="es-es">Spagna</option><option value="ch-it">Svizzera</option></optgroup>
                            <optgroup label="Americhe"><option value="us-en">USA</option><option value="ca-en">Canada</option><option value="br-pt">Brasile</option><option value="mx-es">Messico</option></optgroup>
                            <option value="wt-wt">Global / Worldwide</option>
                        </select>
                        <select id="dork-preset" style="background:#000; color:white; border:1px solid #333; padding:10px;">
                            <optgroup label="Social & People Recon">
                                <option value='site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:twitter.com OR site:tiktok.com "target"'>Tutti i Social</option>
                                <option value='site:linkedin.com "target"'>LinkedIn</option>
                                <option value='site:t.me "target"'>Telegram Channels</option>
                            </optgroup>
                            <optgroup label="Files & Data Leak">
                                <option value='filetype:pdf "target"'>PDF Docs</option>
                                <option value='filetype:xls OR filetype:xlsx "target"'>Excel DBs</option>
                            </optgroup>
                        </select>
                        <button class="btn" onclick="execDork()" style="background:#333">📡 LANCIATI DORK</button>
                    </div>
                </div>
            </div>
            <div id="progress-container"><div id="progress-bar"></div></div>
            <div class="results-area"><div id="results-container"></div></div>
        </div>
    </div>

    <div id="ctx-menu">
        <div class="ctx-item" onclick="saveTarget()">💾 Salva in Cronologia</div>
        <div class="ctx-item" onclick="openProfile()">🔗 Visita Profilo</div>
        <div class="ctx-item" onclick="downloadProfilePic()">📥 Scarica Immagine</div>
    </div>

    <script>
        let currentData = null; let historyDb = {}; const socialIcons = {{social_map|tojson}};

        function linkify(text) {
            const urlRegex = /(https?:\/\/[^\s<,]+)/g;
            const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
            
            let linkedText = String(text).replace(urlRegex, (url) => {
                return `<a href="${url}" target="_blank" onclick="event.stopPropagation()">${url}</a>`;
            });
            
            linkedText = linkedText.replace(emailRegex, (email) => {
                return `<a href="mailto:${email}" onclick="event.stopPropagation()">${email}</a>`;
            });
            
            return linkedText;
        }

        function loadCredsFile(input) {
            const file = input.files[0]; const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = JSON.parse(e.target.result);
                    if(data.sid) document.getElementById('sid-input').value = data.sid;
                    if(data.tg_id) document.getElementById('tg-id').value = data.tg_id;
                    if(data.tg_hash) document.getElementById('tg-hash').value = data.tg_hash;
                    alert("✅ Credenziali caricate!");
                } catch(err) { alert("❌ Errore JSON."); }
            }; reader.readAsText(file);
        }

        function startApp() {
            const sid = document.getElementById('sid-input').value;
            const tg_id = document.getElementById('tg-id').value;
            const tg_hash = document.getElementById('tg-hash').value;
            fetch('/api/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({sid, tg_id, tg_hash}) });
            document.getElementById('login-view').style.display = 'none';
            document.getElementById('dashboard').style.display = 'flex';
        }

        function toggleDorkUI() { document.getElementById('dork-country').disabled = (document.getElementById('dork-engine').value !== 'duckduckgo'); }

        async function runSearch(mode) {
            const target = document.getElementById('main-search').value.trim(); if(!target) return;
            document.getElementById('results-container').innerHTML = '';
            document.getElementById('progress-container').style.display = 'block';

            if (mode === 'global') {
                const platforms = Object.keys(socialIcons);
                let completed = 0;
                platforms.forEach(async (plat) => {
                    try {
                        const r = await fetch('/api/search', { 
                            method: 'POST', 
                            headers: {'Content-Type':'application/json'}, 
                            body: JSON.stringify({target, mode: 'single', platform: plat}) 
                        });
                        const d = await r.json();
                        if(d && !d.Error) renderCard(d);
                    } catch(e) {}
                    completed++;
                    if(completed === platforms.length) document.getElementById('progress-container').style.display = 'none';
                });
            } else {
                const r = await fetch('/api/search', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({target, mode}) });
                const d = await r.json();
                document.getElementById('progress-container').style.display = 'none';
                if(d.Error) return alert(d.Error);
                renderCard(d);
            }
        }

        function renderCard(d) {
            const container = document.getElementById('results-container'); 
            let items = '';
            for(let k in d.info) {
                const val = linkify(d.info[k]);
                items += `<div class="data-box ${k.includes('Obf')?'gold':''}"><label>${k}</label><span>${val}</span></div>`;
            }

            const platIcon = socialIcons[d.type] ? socialIcons[d.type].icon : socialIcons["Instagram"].icon;
            let statusIconsHtml = '';
            if(d.type === "Phone" || d.info["WhatsApp"]) {
                const isWa = d.info["WhatsApp"] === "Attivo"; 
                const isTg = d.info["Telegram"] && d.info["Telegram"].includes("Registrato");
                statusIconsHtml = `<div style="display:flex; gap:12px; margin-top:8px;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3670/3670051.png" style="width:24px; opacity:${isWa?1:0.2}; cursor:pointer" onclick="event.stopPropagation(); window.open('https://wa.me/${d.username.replace(/\+/g,'')}', '_blank')">
                    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png" style="width:24px; opacity:${isTg?1:0.2}; cursor:pointer" onclick="event.stopPropagation(); window.open('https://t.me/+${d.username.replace(/\+/g,'')}', '_blank')">
                </div>`;
            }

            const card = document.createElement('div'); 
            card.className = 'res-card';
            card.onclick = () => card.classList.toggle('open');
            card.oncontextmenu = (e) => { 
                e.preventDefault(); e.stopPropagation();
                currentData = d; 
                const m = document.getElementById('ctx-menu'); 
                m.style.display = 'block'; m.style.left = e.pageX + 'px'; m.style.top = e.pageY + 'px'; 
            };

            card.innerHTML = `
                <div class="card-top">
                    <div class="profile-img-container">
                        <img class="main-pfp" src="${d.main_img}" onerror="this.src='${platIcon}'">
                        <img src="${platIcon}" class="social-mini-icon">
                    </div>
                    <div>
                        <h3 style="margin:0; color:var(--accent); font-size: 18px;">@${d.username}</h3>
                        <small style="opacity:0.6; font-size: 12px;">${d.type} Intelligence</small>
                        ${statusIconsHtml}
                    </div>
                </div>
                <div class="card-body">${items}</div>
            `;
            container.prepend(card);
        }

        document.onclick = () => document.getElementById('ctx-menu').style.display = 'none';

        function saveTarget() {
            const id = "H_" + Date.now(); historyDb[id] = currentData; const list = document.getElementById('hist-list');
            const div = document.createElement('div'); div.className = 'hist-card';
            div.innerHTML = `<div style="display:flex;align-items:center;gap:12px;"><input type="checkbox" class="h-check" value="${id}"><img src="${currentData.main_img}" width="35" height="35" style="border-radius:50%"><b>@${currentData.username}</b></div>`;
            list.prepend(div);
        }

        function downloadProfilePic() { if(!currentData) return; const a = document.createElement('a'); a.href = currentData.main_img; a.download = `OSINT_${currentData.username}.jpg`; a.click(); }
        function openProfile() { if(currentData.url) window.open(currentData.url, '_blank'); }
        function execDork() { const t = document.getElementById('main-search').value; const e = document.getElementById('dork-engine').value; const c = document.getElementById('dork-country').value; const p = document.getElementById('dork-preset').value; let url = e === 'duckduckgo' ? `https://duckduckgo.com/?q=${encodeURIComponent(p.replace('target', t))}&kl=${c}` : `https://www.google.it/search?q=${encodeURIComponent(p.replace('target', t))}`; window.open(url, '_blank'); }
        
        async function buildReport() {
            const selectedIds = Array.from(document.querySelectorAll('.h-check:checked')).map(cb => cb.value);
            if(selectedIds.length === 0) return alert("Seleziona target.");
            const format = document.getElementById('export-format').value; const targets = selectedIds.map(id => historyDb[id]);
            const r = await fetch('/api/export', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({targets, format}) });
            const blob = await r.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `Report.${format === 'excel' ? 'xlsx' : 'pdf'}`; a.click();
        }
    </script>
</body>
</html>
"""

# --- BACKEND ---
@app.route('/')
def index(): return render_template_string(HTML_UI, creds=core.creds, social_map=SOCIAL_MAP, logo_url=LOGO_URL)

@app.route('/api/login', methods=['POST'])
def login(): core.save_creds(request.json); return jsonify({"ok": True})

def get_b64_image(url_or_bytes):
    if not url_or_bytes: return ""
    try:
        if isinstance(url_or_bytes, bytes): return f"data:image/jpeg;base64,{base64.b64encode(url_or_bytes).decode()}"
        if url_or_bytes.startswith('http'):
            r = session.get(url_or_bytes, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200: return f"data:image/jpeg;base64,{base64.b64encode(r.content).decode()}"
    except: pass
    return str(url_or_bytes)

def scrape_metadata(url, platform_name=""):
    try:
        r = session.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OSINT-Bot/2.1"})
        html = r.text
        
        img = re.search(r'property="(?:og:image|twitter:image)"\s+content="([^"]+)"', html)
        desc = re.search(r'property="(?:og:description|twitter:description)"\s+content="([^"]+)"', html)
        title = re.search(r'<title>(.*?)</title>', html)
        
        pfp = get_b64_image(img.group(1)) if img else ""
        meta_dict = {}

        meta_dict["Bio/Descrizione"] = (desc.group(1) if desc else "Nessuna descrizione rilevata.")
        if title: meta_dict["Titolo Pagina"] = title.group(1).strip()

        if platform_name == "GitHub":
            foll = re.search(r'([0-9,k.]+)</span>\s+followers', html)
            foll_ing = re.search(r'([0-9,k.]+)</span>\s+following', html)
            loc = re.search(r'itemprop="homeLocation"[^>]*>.*?<span[^>]*>(.*?)</span>', html, re.S)
            blog = re.search(r'itemprop="url"[^>]*>(.*?)</a>', html)
            if foll: meta_dict["Followers"] = foll.group(1)
            if foll_ing: meta_dict["Following"] = foll_ing.group(1)
            if loc: meta_dict["Località"] = loc.group(1).strip()
            if blog: meta_dict["Sito Web"] = blog.group(1).strip()
            
        elif platform_name == "YouTube":
            subs = re.search(r'"subscriberCountText":"(.*?)"', html)
            if subs: meta_dict["Iscritti"] = subs.group(1)

        elif platform_name == "TikTok":
            f_count = re.search(r'"followerCount":([0-9]+)', html)
            l_count = re.search(r'"heart":([0-9]+)', html)
            if f_count: meta_dict["Followers"] = f_count.group(1)
            if l_count: meta_dict["Likes"] = l_count.group(1)

        elif platform_name == "Reddit":
            karma = re.search(r'"commentKarma":(\d+),"linkKarma":(\d+)', html)
            if karma: meta_dict["Karma"] = f"Post: {karma.group(2)} | Comm: {karma.group(1)}"

        emails_found = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html[:25000])))
        if emails_found: meta_dict["Email Rilevate"] = " ".join(emails_found[:5])

        all_raw_links = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
        blacklist = ['githubassets.com', 'google.com', 'gstatic.com', 'facebook.com/tr', 'schema.org', 'w3.org', 'api.instagram.com', 'apple.com', 'microsoft.com', 'doubleclick.net', 'googletagmanager.com', 'google-analytics.com', 'github.com/login', 'github.com/join']
        known_socials = ["instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com", "t.me", "wa.me", "discord", "twitch", "linktr.ee", "threads.net", "bsky.app"]
        
        social_links = []
        external_links = []
        processed = set()

        for link in all_raw_links:
            clean_link = link.rstrip('/').split('?')[0]
            if clean_link in processed or any(b in clean_link.lower() for b in blacklist) or clean_link.lower() == url.lower().rstrip('/'):
                continue
            
            is_social = any(s in clean_link.lower() for s in known_socials)
            if is_social:
                social_links.append(clean_link)
            else:
                if not any(ext in clean_link.lower() for ext in ['.css', '.js', '.png', '.jpg', '.svg', '.json']):
                    external_links.append(clean_link)
            processed.add(clean_link)

        if social_links: meta_dict["Social Collegati"] = " ".join(list(set(social_links))[:10])
        if external_links: meta_dict["Siti Esterni"] = " ".join(list(set(external_links))[:5])

        return pfp, meta_dict
    except: return "", {"Stato": "Profilo attivo (Errore analisi dettagli)"}

@app.route('/api/search', methods=['POST'])
def search_logic():
    data = request.json; target = data.get('target'); mode = data.get('mode')
    try:
        cookies = {"sessionid": core.creds['sid']} if core.creds['sid'] else {}
        headers_ig = {"X-IG-App-ID": APP_ID_WEBPROFILE, "User-Agent": "Instagram 292.0.0.17.111 Android"}
        
        if mode == 'ig' or (mode == 'single' and data.get('platform') == 'Instagram'):
            r = session.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={target}", headers=headers_ig, cookies=cookies, timeout=10)
            u = r.json().get('data', {}).get('user')
            if not u: return jsonify({"Error": "Not found"})
            lookup = core.instagram_lookup(target)
            info = {
                "Nome": u.get('full_name'), "ID": u.get('id'), "Followers": u.get('edge_followed_by', {}).get('count'),
                "Privacy": "🔒 Privato" if u.get('is_private') else "🔓 Pubblico", "Tipo Account": "💼 Professionale" if u.get('is_professional_account') else "👤 Personale",
                "Categoria": u.get('category_name') or "N/D", "Verificato": "✔️ Sì" if u.get('is_verified') else "❌ No",
                "Account Recente": "⚠️ Sì" if u.get('is_joined_recently') else "📅 No", "Link Bio": u.get('external_url') or "Nessuno",
                "Email Obf": lookup.get('Email Obf', 'N/A'), "Phone Obf": lookup.get('Phone Obf', 'N/A')
            }
            return jsonify({"username": u['username'], "type": "Instagram", "url": f"https://instagram.com/{target}", "main_img": get_b64_image(u.get('profile_pic_url_hd')), "info": info})
        
        elif mode == 'single':
            name = data.get('platform'); config = SOCIAL_MAP.get(name)
            url = f"https://www.{config['base']}{target}"
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                img, meta_data = scrape_metadata(url, name)
                return jsonify({"username": target, "type": name, "url": url, "main_img": img if img else config["icon"], "info": meta_data})
            return jsonify({"Error": "Not found"})

        elif mode == 'phone':
            clean = target if target.startswith('+') else '+' + target
            p = phonenumbers.parse(clean); c_name = geocoder.description_for_number(p, "it")
            res = {"username": target, "type": "Phone", "url": f"https://wa.me/{target.replace('+','')}", "main_img": "https://cdn-icons-png.flaticon.com/512/724/724664.png", "info": {"Nazione": c_name, "Operatore": carrier.name_for_number(p, "it"), "WhatsApp": "Attivo"}}
            if core.creds['tg_id']:
                async def tg_scan():
                    client = TelegramClient('session', core.creds['tg_id'], core.creds['tg_hash'])
                    await client.connect()
                    if await client.is_user_authorized():
                        r = await client(ImportContactsRequest([InputPhoneContact(client_id=0, phone=clean, first_name="Target", last_name="")]))
                        if r.users:
                            u = r.users[0]; res['info']['Telegram'] = f"Registrato: {u.first_name}"; res['type'] = "Telegram"
                            if u.photo: res['main_img'] = get_b64_image(await client.download_profile_photo(u, bytes))
                    await client.disconnect()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop); loop.run_until_complete(tg_scan())
            return jsonify(res)
            
    except Exception as e: return jsonify({"Error": str(e)})

@app.route('/api/export', methods=['POST'])
def export_report():
    data = request.json; targets = data.get('targets'); fmt = data.get('format')
    if fmt == 'pdf':
        pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15)
        for t in targets:
            pdf.add_page(); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"Report: @{t['username']}", 0, 1)
            pdf.set_font("Arial", '', 10)
            for k, v in t['info'].items(): pdf.cell(0, 6, f"{k}: {v}", 0, 1)
        return send_file(io.BytesIO(pdf.output()), download_name="Report.pdf", as_attachment=True)
    elif fmt == 'excel':
        df = pd.DataFrame([ {**{"Username": t['username'], "Tipo": t['type']}, **t['info']} for t in targets ])
        buf = io.BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
        return send_file(buf, download_name="Data.xlsx", as_attachment=True)

if __name__ == "__main__":
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open("http://127.0.0.1:5050")), daemon=True).start()
    app.run(port=5050)
