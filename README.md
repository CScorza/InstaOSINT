![screen](https://github.com/user-attachments/assets/11fc48df-85c3-4f0e-b429-b58d14f1abc6)

## 🚀 OSINT Tool per l'Analisi di Profili Instagram e Ricerca Globale

Framework avanzato di Open Source Intelligence (OSINT) sviluppato per investigatori digitali e appassionati di sicurezza informatica. 
Il tool offre un'interfaccia web moderna per centralizzare la ricerca di informazioni su oltre 40 piattaforme social, numeri di telefono e profili Instagram.

*Advanced Open Source Intelligence (OSINT) framework developed for digital investigators and cybersecurity enthusiasts. The tool offers a modern web interface to centralize information gathering across over 40 social platforms, phone numbers, and Instagram profiles.*

<img width="1683" height="721" alt="image" src="https://github.com/user-attachments/assets/db0b4a74-aa6a-4298-a075-2c6e9ab6e1bd" />

### 🚀 Caratteristiche Principali | Key Features

- Instagram Intelligence/: 

   - Estrazione di metadati, stato privacy, categoria account e recupero di email/telefoni offuscati tramite API private.
   - *Metadata extraction, privacy status, and recovery of obfuscated emails/phones.*

- Global Social Scanner:
   - Ricerca simultanea di uno username su 45+ piattaforme (GitHub, TikTok, LinkedIn, X, etc.) con scraping dei metadati.
   - *Simultaneous search across 45+ platforms with metadata scraping.*

- Phone Lookup & Messaging OSINT:

  -  WhatsApp:
      - Verifica dello stato di attività del numero.
      - *Verification and Telegram API integration (ID, name, profile pic).*

  - Telegram:
    - Integrazione con le API ufficiali per identificare l'ID utente, il nome registrato e scaricare la foto profilo.
    - *Integration with official APIs to identify user ID, registered name and download profile photo.*

- Dorking Engine: 
    - Integrazione di dork preimpostati per trovare leak di documenti (PDF, Excel) o profili social specifici.
    - *Integration of pre-built dorks to find leaks of specific documents (PDF, Excel) or social profiles.*

- Reporting Professionale: 
  - Generazione istantanea di report in formato PDF, Word o Excel 
  - *Instantly generate reports in PDF, Word, or Excel formats*

### 🛠️ Setup
Il tool include una funzione di Auto-Setup che gestisce autonomamente l'ambiente virtuale (venv) e le dipendenze.
*The tool includes an Auto-Setup feature that automatically manages the virtual environment (venv) and dependencies.*

<img width="978" height="768" alt="image" src="https://github.com/user-attachments/assets/986a7a7c-49b1-4164-97ee-e9b02878cb25" />

Clone the repository:

```
git clone https://github.com/tuo-username/cscorza-instaosint-pro.git
cd cscorza-instaosint-pro
```
Run the script:
```
python3 InstaOSINT.py
```
### 📖 Guida alle Credenziali
Per sbloccare il pieno potenziale del tool (funzioni Instagram e Telegram), è necessario configurare alcuni parametri.
*To unlock the full potential of the tool (Instagram and Telegram features), you need to configure some parameters.*

1. Come ottenere l'Instagram SessionID/How to get your Instagram Session ID

```
Il sessionid permette al tool di interrogare le API di Instagram simulando un accesso autenticato.
The sessionid allows the tool to query Instagram APIs by simulating authenticated access.

1. Accedi a Instagram.com dal tuo browser (Chrome/Edge/Firefox)/Go to Instagram.com from your browser (Chrome/Edge/Firefox).

2. Premi F12 o tasto destro -> Ispeziona./Press F12 or right-click -> Inspect.

3. Vai nella scheda Applicazione (o Storage su Firefox)./Go to the Application tab (or Storage in Firefox).

4. Nel menu a sinistra, espandi Cookie e seleziona https://www.instagram.com./In the left menu, expand Cookies and select https://www.instagram.com.

5. Cerca nella lista il nome sessionid e copia il valore nella colonna Value./Find the name sessionid in the list and copy the value into the Value column.
```
2. Come ottenere Telegram API ID e Hash/ How to get Telegram API ID
```
Questi parametri sono necessari per la scansione dei numeri di telefono tramite la libreria Telethon.
These parameters are required for scanning phone numbers using the Telethon library.

1. Accedi al portale my.telegram.org./Log in to my.telegram.org.

2. Inserisci il tuo numero di telefono e il codice di conferma ricevuto su Telegram./Enter your phone number and the confirmation code you received on Telegram.

3. Clicca su API development tools./Click on API development tools.

4. Crea una nuova applicazione (puoi usare nomi casuali)./Create a new application (you can use random names).

5. Copia l'App api_id e l'App api_hash./Copy the App api_id and the App api_hash.

```

###🐧Linux (Ambiente Ottimizzato)
Il tool è stato testato e ottimizzato per distribuzioni Linux.The tool has been tested and optimized for Linux distributions.

**CScorza OSINT Specialist**

|GitHub:|CScorza|
| :--- | :--- |
|X / Twitter:| @CScorzaOSINT|
|BlueSky:|cscorza.bsky.social|
|Telegram:| @CScorzaOSINT|
|Website:| cscorza.github.io|
|Email:|cscorzaosint@protonmail.com|

☕ Supporta il Progetto/Support

|BTC:| bc1qfn9kynt7k26eaxk4tc67q2hjuzhfcmutzq2q6a|
| :--- | :--- |
|TON:| UQBtLB6m-7q8j9Y81FeccBEjccvl34Ag5tWaUD|
