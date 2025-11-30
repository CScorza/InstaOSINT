

# 🕵️ CScorza - InstaOSINT
## 🚀 OSINT Tool per l'Analisi di Profili Instagram e Ricerca Globale

## 🇮🇹 ITALIANO: Dettagli del Progetto

### Avvio e Configurazione

Lo script è progettato per essere totalmente **autonomo**. 
Alla prima esecuzione, verifica la presenza delle librerie necessarie e crea automaticamente un ambiente virtuale isolato (`Virtualenv*`) per installare le dipendenze, garantendo che il tuo ambiente di sistema rimanga pulito.

Per avviare lo strumento, esegui il file principale dal tuo terminale:

````
python InstaOSINT.py
````

Al primo avvio, lo script eseguirà i seguenti passaggi (visualizzati nel terminale):

1.  **Verifica e Installazione Venv:** Creazione della cartella `VirtualenvInstaOSINT` e installazione delle librerie necessarie (`requests`, `Pillow`, `ttkthemes`, `phonenumbers`, etc.).
2.  **Rilancio:** Lo script si auto-rilancerà all'interno di questo ambiente virtuale per garantire la corretta esecuzione della GUI.

### Funzionalità Principali della GUI

| Categoria | Funzionalità | Descrizione |
| :--- | :--- | :--- |
| **Instagram Actions** | **User Info / ID Info** | Ottiene informazioni dettagliate (follower, bio, URL dell'immagine, conteggio post) tramite l'username o l'ID numerico. |
| | **Esplora Profilo** | Apre direttamente l'URL del profilo Instagram nel browser predefinito. |
| **Global Search** | **Phone Search** | Analizza un numero di telefono internazionale (`+XX...`) fornendo validità, operatore, tipo di linea e link diretti per WhatsApp e Telegram. |
| | **Username Search** | Esegue una verifica incrociata rapida per lo username fornito su oltre 15 piattaforme social (Facebook, Twitter/X, GitHub, TikTok, ecc.), mostrando i link trovati. |
| | **Salvataggio Avanzato** | Permette di salvare i risultati ottenuti in locale nei formati **JSON, TXT, o CSV** (compatibile con Excel), con scelta del percorso tramite `filedialog`. |

### 🔑 Come Ricavare il SessionID di Instagram

L'uso di un SessionID valido è **opzionale ma fortemente raccomandato** in quanto consente allo script di accedere a dati altrimenti nascosti o offuscati (come email/telefono parziali) che Instagram non rende disponibili agli utenti non autenticati o disconnessi.

**Istruzioni per il SessionID:**

1.  Accedi a Instagram tramite un **browser web** (Chrome, Firefox, ecc.).
2.  Apri gli **Strumenti per Sviluppatori** (solitamente premendo **F12**).
3.  Vai alla scheda **Applicazione** (o Archiviazione/Storage) e seleziona **Cookie**.
4.  Cerca la chiave denominata **`sessionid`** e copia il lungo valore alfanumerico associato.
5.  Incolla questo valore nel campo SessionID dello script. Verrà salvato in locale nel file `sessionid.txt` per gli avvii futuri.

-----

## 🇬🇧 ENGLISH: Project Details

### Getting Started and Setup*

*The script is designed to be **fully self-contained**. On its first run, it checks for necessary libraries and automatically creates an isolated virtual environment (`Virtualenv*`) to install dependencies, ensuring your system environment remains clean.*

*To start the tool, run the main file from your terminal:*

```
python InstaOSINT.py
```

*On first run, the script will perform the following steps (visible in the terminal):*
*1. **Venv Check & Installation:** Creation of the `VirtualenvInstaOSINT` folder and installation of required libraries (`requests`, `Pillow`, `ttkthemes`, `phonenumbers`, etc.).*
\*2. **Relaunch:** *The script will automatically relaunch itself within this virtual environment to guarantee proper GUI execution.*

### Key GUI Features

| *Category* | *Feature* | *Description* |
| :--- | :--- | :--- |
| *Instagram Actions* | *User Info / ID Info* | *Retrieves detailed information (followers, bio, image URL, post count) using the username or numeric ID.* |
| | *Explore Profile* | *Directly opens the Instagram profile URL in your default browser.* |
| *Global Search* | *Phone Search* | *Analyzes an international phone number (`+XX...`) providing validity, operator, line type, and direct links for WhatsApp and Telegram.* |
| | *Username Search* | *Performs a quick cross-check for the provided username across over 15 major social media platforms (Facebook, Twitter/X, GitHub, TikTok, etc.), displaying found links.* |
| | *Advanced Saving* | *Allows saving the results locally in **JSON, TXT, or CSV** (Excel compatible) formats, with path selection via `filedialog`.* |

### 🔑 How to Retrieve Your Instagram SessionID*

*Using a valid SessionID is **optional but highly recommended** as it allows the script to access data otherwise hidden or obfuscated (like partial email/phone numbers) that Instagram does not make available to logged-out or unauthenticated users.*

*1. Log into Instagram using a **web browser** (Chrome, Firefox, etc.).*
*2. Open **Developer Tools** (usually by pressing **F12**).*
*3. Navigate to the **Application** (or Storage) tab and select **Cookies**.*
*4. Look for the key named **`sessionid`** and copy the associated long alphanumeric value.*
*5. Paste this value into the SessionID field of the script. It will be saved locally in `sessionid.txt` for future launches.*

-----

## 🙏 Credits and Acknowledgements

This project was built upon foundational work in the field of OSINT analysis.

Special thanks to **Megadose** and their powerful tool **Toutatis**, which served as inspiration and a foundational base for developing some core analysis logic within this project.
