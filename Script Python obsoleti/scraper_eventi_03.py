import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import queue # Per la comunicazione thread-safe
import os
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import requests

# --- Coda globale per gli aggiornamenti della GUI (comunicazione thread-safe) ---
output_queue = queue.Queue()

# --- Funzione helper per inviare messaggi alla GUI ---
def log_to_gui(message, is_error=False):
    """Invia un messaggio alla coda per essere visualizzato nella GUI."""
    output_queue.put((message, is_error))

# -----------------------
# SETUP DRIVER SELENIUM (per le fonti che richiedono Selenium in headless)
# -----------------------
def setup_driver():
    options = Options()
    # ⚠️ ASSICURATI CHE QUESTO PERCORSO SIA CORRETTO PER LA TUA INSTALLAZIONE DI CHROME
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# -----------------------
# SETUP DRIVER PERSISTENTE (per Winetourism con CAPTCHA, visibile la prima volta)
# -----------------------
def setup_driver_persistente():
    options = Options()
    # ⚠️ ASSICURATI CHE QUESTO PERCORSO SIA CORRETTO PER LA TUA INSTALLAZIONE DI CHROME
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Browser visibile per completare CAPTCHA la prima volta, poi riusa il profilo
    # options.add_argument("--headless=new")  # Lasciato commentato per Cloudflare per renderlo visibile
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

    # Percorso cartella profilo persistente (cookie + cache)
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")

    # Imposta una dimensione finestra grande per catturare più contenuto in uno screenshot
    options.add_argument("--window-size=1920,3000") # Larghezza, Altezza

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# -----------------------
# SCRAPER VISIT LAZIO
# -----------------------
def scrape_visitlazio(max_eventi):
    log_to_gui("🔹 Scraping VisitLazio...")
    driver = setup_driver()
    driver.get("https://www.visitlazio.com/web/eventi")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover"))
        )
        time.sleep(2)
    except:
        log_to_gui("❌ Timeout VisitLazio", is_error=True)
        driver.quit()
        return []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    event_links = soup.select("a.mec-color-hover")
    if max_eventi > 0:
        event_links = event_links[:max_eventi]
    eventi = []
    for a in event_links:
        titolo = a.get_text(strip=True)
        link = a['href']
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Attività varie",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (luogo_generico.get_text(strip=True) if luogo_generico else ""),
            "Prezzo": "Consulta sito",
            "Link": link,
            "Fonte": "VisitLazio"
        })
    driver.quit()
    log_to_gui(f"✅ Estratti {len(eventi)} eventi da VisitLazio.")
    return eventi

# -----------------------
# SCRAPER EVENTBRITE
# -----------------------
def scrape_eventbrite(max_eventi):
    log_to_gui("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)
    elementi = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    links = list({el.get_attribute("href") for el in elementi if el.get_attribute("href")})
    eventi = []
    for link in links[:max_eventi if max_eventi > 0 else len(links)]:
        driver.get(link)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            titolo = driver.find_element(By.TAG_NAME, "h1").text.strip()
            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Attività varie",
                "Data Inizio": "Consulta sito",
                "Data Fine": "Consulta sito",
                "Orario": "Consulta sito",
                "Luogo": "Consulta sito",
                "Prezzo": "Consulta sito",
                "Link": link,
                "Fonte": "Eventbrite"
            })
        except:
            continue
    driver.quit()
    log_to_gui(f"✅ Estratti {len(eventi)} eventi da Eventbrite.")
    return eventi

# -----------------------
# SCRAPER WINERIES EXPERIENCE
# -----------------------
def scrape_wineriesexperience(max_eventi):
    log_to_gui("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    url_base = "https://wineriesexperience.it"
    driver.get(f"{url_base}/collections/degustazioni-vini-lazio")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.select("a.product-grid-item--link")
    eventi = []
    for a in links[:max_eventi if max_eventi > 0 else len(links)]:
        href = a['href']
        link = url_base + href
        driver.get(link)
        time.sleep(2)
        page = BeautifulSoup(driver.page_source, 'html.parser')
        titolo = page.find("h1").text.strip() if page.find("h1") else ""
        prezzo_tag = page.find("span", attrs={"data-product-price": True})
        prezzo = prezzo_tag.text.strip() if prezzo_tag else "consulta sito"
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "Consulta sito",
            "Luogo": "Consulta sito",
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })
    driver.quit()
    log_to_gui(f"✅ Estratti {len(eventi)} eventi da WineriesExperience.")
    return eventi

# -----------------------
# SCRAPER WINEDERING
# -----------------------
def scrape_winedering_latium(max_eventi=20):
    log_to_gui("🔹 Scraping Winedering Lazio...")
    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        log_to_gui(f"❌ Errore HTTP: {response.status_code}", is_error=True)
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    schede = soup.select("div.col-lg-3.col-md-6.col-sm-6.col-xs-6.pad-v.thumb.item")
    eventi = []
    for scheda in schede[:max_eventi if max_eventi > 0 else len(schede)]:
        titolo_tag = scheda.select_one("h3.name a")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        link = "https://www.winedering.com" + titolo_tag.get("href", "") if titolo_tag else url
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "Consulta sito",
            "Luogo": "Consulta sito",
            "Prezzo": "Consulta sito",
            "Link": link,
            "Fonte": "Winedering"
        })
    log_to_gui(f"✅ Estratti {len(eventi)} eventi da Winedering.")
    return eventi

# -----------------------
# SCRAPER WINETOURISM LAZIO
# -----------------------
def scrape_winetourism_lazio(max_eventi=0):
    log_to_gui("🔹 Scraping Winetourism.com – Lazio (profilo persistente + BeautifulSoup)...")
    
    driver = setup_driver_persistente()
    
    eventi = [] 
    url_listato = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
    driver.get(url_listato)

    log_to_gui("⚠️ Se appare il CAPTCHA di Cloudflare, completalo manualmente ORA.")
    time.sleep(15)  

    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All')]"))
        )
        accept_button.click()
        log_to_gui("✅ Popup cookie 'Accept All' chiuso.")
    except:
        try:
            decline_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Decline All')]"))
            )
            decline_button.click()
            log_to_gui("✅ Popup cookie 'Decline All' chiuso.")
        except:
            log_to_gui("ℹ️ Nessun popup cookie trovato o già chiuso.")
    time.sleep(2) 

    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 20 
    while True and scroll_attempts < max_scroll_attempts:
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);") 
        time.sleep(2) 
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            log_to_gui("⬆️ Raggiunta la fine dello scroll o nessun nuovo contenuto caricato.")
            break
        last_height = new_height
        scroll_attempts += 1
        log_to_gui(f"   Scroll: {new_height}px (tentativo {scroll_attempts}/{max_scroll_attempts})")

    listato_soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    cards_on_list_page = listato_soup.select("div.item-content.ml-3.d-flex.flex-column")
    log_to_gui(f"📌 Trovate {len(cards_on_list_page)} card sulla pagina di listato.")

    for i, card_content_div in enumerate(cards_on_list_page):
        if max_eventi > 0 and len(eventi) >= max_eventi:
            break

        luogo_tag = card_content_div.select_one("span.position-text")
        luogo = luogo_tag.get_text(strip=True) if luogo_tag else "Lazio, Italia"
        luogo = re.sub(r"・.*$", "", luogo).strip() 

        prezzo_tag = card_content_div.select_one("p.price")
        prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "Non trovato"

        link_tag = card_content_div.select_one('a.item-link')
        link_dettaglio = link_tag['href'] if link_tag and 'href' in link_tag.attrs else url_listato
        if not link_dettaglio.startswith("http"):
            link_dettaglio = "https://www.winetourism.com" + link_dettaglio

        log_to_gui(f"   Navigazione al link di dettaglio per la card {i+1}: {link_dettaglio}")
        driver.get(link_dettaglio)
        time.sleep(3) 

        dettaglio_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        titolo_tag_h1 = dettaglio_soup.select_one("h1#experience-title")
        titolo = ""
        if titolo_tag_h1:
            titolo = titolo_tag_h1.get_text(strip=True)
        if not titolo: 
            titolo = "Senza titolo (dettaglio)"


        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": luogo,
            "Prezzo": prezzo,
            "Link": link_dettaglio,
            "Fonte": "Winetourism.com"
        })
    
    driver.quit() 
    log_to_gui(f"✅ Estratti {len(eventi)} eventi da Winetourism.com (BeautifulSoup)")
    return eventi

# -----------------------
# LOGICA DI SCRAPING PRINCIPALE (eseguita in un thread separato)
# -----------------------
def run_scraping_logic(max_lazio, max_eventbrite, max_wineries, max_winedering, max_winetourism,
                        keyword_filter, min_price_filter, max_price_filter):
    
    log_to_gui("🚀 Avvio dello script di scraping...")
    
    all_eventi = []
    try:
        eventi_lazio = scrape_visitlazio(max_eventi=max_lazio)
        all_eventi.extend(eventi_lazio)
    except Exception as e:
        log_to_gui(f"❌ Errore durante scraping VisitLazio: {e}", is_error=True)
    
    try:
        eventi_eventbrite = scrape_eventbrite(max_eventi=max_eventbrite)
        all_eventi.extend(eventi_eventbrite)
    except Exception as e:
        log_to_gui(f"❌ Errore durante scraping Eventbrite: {e}", is_error=True)

    try:
        eventi_wineries = scrape_wineriesexperience(max_eventi=max_wineries)
        all_eventi.extend(eventi_wineries)
    except Exception as e:
        log_to_gui(f"❌ Errore durante scraping WineriesExperience: {e}", is_error=True)

    try:
        eventi_winedering = scrape_winedering_latium(max_eventi=max_winedering)
        all_eventi.extend(eventi_winedering)
    except Exception as e:
        log_to_gui(f"❌ Errore durante scraping Winedering: {e}", is_error=True)

    try:
        eventi_winetourism = scrape_winetourism_lazio(max_eventi=max_winetourism)
        all_eventi.extend(eventi_winetourism)
    except Exception as e:
        log_to_gui(f"❌ Errore durante scraping Winetourism: {e}", is_error=True)

    if not all_eventi:
        log_to_gui("\nℹ️ Nessun evento estratto da nessuna fonte.", is_error=False)
        log_to_gui("🏁 Scraping completato!", is_error=False)
        return # Termina se non ci sono eventi

    # --- APPLICAZIONE FILTRI AI DATI ESTRATTI ---
    log_to_gui("\n⚙️ Applicazione filtri ai dati estratti...")
    df = pd.DataFrame(all_eventi)

    # Pulizia e conversione 'Prezzo' per il filtro numerico
    def clean_price(price_str):
        if isinstance(price_str, str):
            price_str = price_str.lower().replace('from', '').replace('da', '').replace('€', '').strip()
            if '-' in price_str: # Gestisce range di prezzo come "42.00 - 60.00"
                parts = price_str.split('-')
                try:
                    return float(parts[0].strip().replace(',', '.')) # Prende il prezzo più basso del range
                except ValueError:
                    pass
            try:
                return float(price_str.replace(',', '.'))
            except ValueError:
                pass
        return None # Ritorna None per prezzi non validi o "Consulta sito"

    df['Prezzo_Numerico'] = df['Prezzo'].apply(clean_price)
    
    df_filtered = df.copy()

    # Filtro per parola chiave (Titolo o Luogo)
    if keyword_filter:
        log_to_gui(f"   Filtro per parola chiave: '{keyword_filter}'")
        df_filtered = df_filtered[
            df_filtered['Titolo'].astype(str).str.contains(keyword_filter, case=False, na=False) |
            df_filtered['Luogo'].astype(str).str.contains(keyword_filter, case=False, na=False)
        ]

    # Filtro per fascia di prezzo
    if min_price_filter is not None or max_price_filter is not None:
        log_to_gui(f"   Filtro per prezzo: Min={min_price_filter if min_price_filter is not None else 'N/A'}, Max={max_price_filter if max_price_filter is not None else 'N/A'}")
        
        # Filtra solo le righe con Prezzo_Numerico valido
        df_valid_prices = df_filtered[df_filtered['Prezzo_Numerico'].notna()]
        
        if min_price_filter is not None:
            df_valid_prices = df_valid_prices[df_valid_prices['Prezzo_Numerico'] >= min_price_filter]
        if max_price_filter is not None:
            df_valid_prices = df_valid_prices[df_valid_prices['Prezzo_Numerico'] <= max_price_filter]
        
        # Le righe senza prezzo numerico valido (es. "Consulta sito") vengono escluse da questo filtro
        df_filtered = df_valid_prices

    log_to_gui(f"✅ Trovati {len(df_filtered)} eventi dopo l'applicazione dei filtri.")

    # --- SALVATAGGIO DEI DATI FILTRATI ---
    os.makedirs("output", exist_ok=True)
    csv_path = os.path.join("output", "eventi_unificati_filtrati.csv") # Salviamo un file filtrato
    excel_path = os.path.join("output", "eventi_unificati_filtrati.xlsx") # E un Excel filtrato
    
    df_filtered.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df_filtered.to_excel(excel_path, index=False)
    log_to_gui(f"\n✅ Salvati {len(df_filtered)} eventi filtrati in CSV ed Excel nella cartella 'output/'.")
    
    log_to_gui("🏁 Scraping e filtraggio completati!", is_error=False)


# -----------------------
# APPLICAZIONE GUI TKINTER
# -----------------------
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wine Scraper GUI")
        self.root.geometry("800x750") # Aumentata l'altezza per i nuovi filtri

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.process_queue) # Avvia il controllo della coda messaggi

    def create_widgets(self):
        # Frame per gli input
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        # Filtri per Max Eventi per Fonte
        tk.Label(input_frame, text="Max eventi per fonte (0 = tutti):", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)

        self.max_entries = {}
        sources = ["VisitLazio", "Eventbrite", "WineriesExperience", "Winedering", "Winetourism.com Lazio"]
        for i, source in enumerate(sources):
            tk.Label(input_frame, text=source + ":").grid(row=i+1, column=0, sticky=tk.W, padx=5, pady=2)
            entry = tk.Entry(input_frame, width=10)
            entry.insert(0, "0") # Valore predefinito "0" (tutti)
            entry.grid(row=i+1, column=1, sticky=tk.W, padx=5, pady=2)
            self.max_entries[source] = entry
        
        # Separatore visivo
        tk.Frame(input_frame, height=2, bd=1, relief=tk.SUNKEN).grid(row=len(sources)+1, column=0, columnspan=3, sticky=tk.EW, pady=10)

        # Filtri Aggiuntivi
        tk.Label(input_frame, text="Filtri Aggiuntivi:", font=("Arial", 10, "bold")).grid(row=len(sources)+2, column=0, columnspan=3, sticky=tk.W, pady=5)

        # Filtro Parola Chiave
        tk.Label(input_frame, text="Parola chiave (Titolo/Luogo):").grid(row=len(sources)+3, column=0, sticky=tk.W, padx=5, pady=2)
        self.keyword_entry = tk.Entry(input_frame, width=30)
        self.keyword_entry.grid(row=len(sources)+3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # Filtro Prezzo Min/Max
        tk.Label(input_frame, text="Prezzo Minimo:").grid(row=len(sources)+4, column=0, sticky=tk.W, padx=5, pady=2)
        self.min_price_entry = tk.Entry(input_frame, width=10)
        self.min_price_entry.grid(row=len(sources)+4, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(input_frame, text="Prezzo Massimo:").grid(row=len(sources)+5, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_price_entry = tk.Entry(input_frame, width=10)
        self.max_price_entry.grid(row=len(sources)+5, column=1, sticky=tk.W, padx=5, pady=2)


        # Pulsante Avvia Scraping
        self.scrape_button = tk.Button(input_frame, text="Avvia Scraping", command=self.start_scraping, font=("Arial", 10, "bold"), bg="green", fg="white")
        self.scrape_button.grid(row=len(sources)+6, column=0, columnspan=3, pady=15)

        # Frame per il Log
        log_frame = tk.Frame(self.root, padx=10, pady=10)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Log Output:", font=("Arial", 10, "bold")).pack(side=tk.TOP, anchor=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=20, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.log_text.tag_config('error', foreground='red') # Tag per errori

    def start_scraping(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END) # Pulisce il log precedente
        self.log_text.config(state=tk.DISABLED)
        
        self.scrape_button.config(state=tk.DISABLED) # Disabilita il pulsante durante lo scraping

        try:
            max_values = {source: int(entry.get()) for source, entry in self.max_entries.items()}
            
            # Recupera i valori dei nuovi filtri
            keyword = self.keyword_entry.get().strip()
            min_price_str = self.min_price_entry.get().strip()
            max_price_str = self.max_price_entry.get().strip()

            min_price = float(min_price_str) if min_price_str else None
            max_price = float(max_price_str) if max_price_str else None

            # Avvia lo scraping in un nuovo thread
            scraping_thread = threading.Thread(target=run_scraping_logic, args=(
                max_values["VisitLazio"],
                max_values["Eventbrite"],
                max_values["WineriesExperience"],
                max_values["Winedering"],
                max_values["Winetourism.com Lazio"],
                keyword,
                min_price,
                max_price
            ))
            scraping_thread.daemon = True 
            scraping_thread.start()
        except ValueError:
            messagebox.showerror("Errore Input", "Per favore, inserisci numeri validi (0 o positivi) per i massimi eventi e per i prezzi.")
            self.scrape_button.config(state=tk.NORMAL) 
        except Exception as e:
            messagebox.showerror("Errore Avvio", f"Si è verificato un errore inatteso all'avvio dello scraping: {e}")
            self.scrape_button.config(state=tk.NORMAL) 

    def process_queue(self):
        """Processa i messaggi dalla coda e aggiorna la GUI."""
        while not output_queue.empty():
            message, is_error = output_queue.get_nowait()
            self.log_text.config(state=tk.NORMAL)
            if is_error:
                self.log_text.insert(tk.END, message + "\n", 'error') 
            else:
                self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END) 
            self.log_text.config(state=tk.DISABLED)
            self.root.update_idletasks() 

        # Riabilita il pulsante se lo scraping è terminato (nessun thread attivo oltre il main)
        # Controlla che nessun thread attivo sia il thread principale o il thread di gestione della coda
        active_threads = [t for t in threading.enumerate() if t.is_alive() and t is not threading.current_thread() and t.name != "TkinterQueueProcessor"]
        if not active_threads and self.scrape_button.cget('state') == tk.DISABLED:
            self.scrape_button.config(state=tk.NORMAL)

        self.root.after(100, self.process_queue) 

    def on_closing(self):
        """Gestisce la chiusura dell'applicazione."""
        # Chiedi conferma solo se ci sono thread di scraping attivi
        active_scraping_threads = [t for t in threading.enumerate() if t.is_alive() and t is not threading.current_thread() and t.name != "TkinterQueueProcessor"]
        if active_scraping_threads:
            if messagebox.askokcancel("Chiudi Applicazione", "Lo scraping è ancora in corso. Sei sicuro di voler chiudere? Verrà interrotto."):
                # In un'applicazione più complessa, si dovrebbe segnalare ai thread di terminare graziosamente
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    # Avvia l'applicazione Tkinter
    root = tk.Tk()
    app = ScraperApp(root)
    # Rinomina il thread principale per distinguerlo dagli altri thread di scraping
    threading.current_thread().name = "TkinterQueueProcessor" 
    root.mainloop()

