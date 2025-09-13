import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import queue
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
import requests

# --- Coda per log GUI ---
output_queue = queue.Queue()
def log_to_gui(message, is_error=False):
    output_queue.put((message, is_error))

# --- Driver Selenium ---
def setup_driver():
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def setup_driver_persistente():
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--user-agent=Mozilla/5.0")
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")
    options.add_argument("--window-size=1920,3000")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# --- Scrapers con deduplicazione interna ---
def scrape_visitlazio(max_eventi):
    log_to_gui("🔹 Scraping VisitLazio...")
    driver = setup_driver()
    driver.get("https://www.visitlazio.com/web/eventi")
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover")))
        time.sleep(2)
    except:
        log_to_gui("❌ Timeout VisitLazio", True)
        driver.quit()
        return []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    event_links = soup.select("a.mec-color-hover")
    if max_eventi > 0:
        event_links = event_links[:max_eventi]

    seen_links = set()
    eventi = []
    for a in event_links:
        titolo = a.get_text(strip=True)
        link = a['href']
        if link in seen_links:
            continue
        seen_links.add(link)
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
    log_to_gui(f"✅ Estratti {len(eventi)} eventi unici da VisitLazio (rimossi {len(event_links)-len(eventi)} duplicati interni).")
    return eventi

def scrape_eventbrite(max_eventi):
    log_to_gui("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)
    elementi = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    links = [el.get_attribute("href") for el in elementi if el.get_attribute("href")]

    seen_links = set()
    unique_links = []
    for l in links:
        if l not in seen_links:
            seen_links.add(l)
            unique_links.append(l)

    eventi = []
    for link in unique_links[:max_eventi if max_eventi > 0 else len(unique_links)]:
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
    log_to_gui(f"✅ Estratti {len(eventi)} eventi unici da Eventbrite (rimossi {len(links)-len(unique_links)} duplicati interni).")
    return eventi

def scrape_wineriesexperience(max_eventi):
    log_to_gui("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    url_base = "https://wineriesexperience.it"
    driver.get(f"{url_base}/collections/degustazioni-vini-lazio")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = [url_base + a['href'] for a in soup.select("a.product-grid-item--link")]

    seen_links = set()
    unique_links = []
    for l in links:
        if l not in seen_links:
            seen_links.add(l)
            unique_links.append(l)

    eventi = []
    for link in unique_links[:max_eventi if max_eventi > 0 else len(unique_links)]:
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
    log_to_gui(f"✅ Estratti {len(eventi)} eventi unici da WineriesExperience (rimossi {len(links)-len(unique_links)} duplicati interni).")
    return eventi

def scrape_winedering_latium(max_eventi=20):
    log_to_gui("🔹 Scraping Winedering Lazio...")
    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        log_to_gui(f"❌ Errore HTTP: {response.status_code}", True)
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    schede = soup.select("div.col-lg-3.col-md-6.col-sm-6.col-xs-6.pad-v.thumb.item")

    eventi = []
    seen_links = set()
    for scheda in schede[:max_eventi if max_eventi > 0 else len(schede)]:
        titolo_tag = scheda.select_one("h3.name a")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        link = "https://www.winedering.com" + titolo_tag.get("href", "") if titolo_tag else url
        if link in seen_links:
            continue
        seen_links.add(link)
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
    log_to_gui(f"✅ Estratti {len(eventi)} eventi unici da Winedering (rimossi {len(schede)-len(eventi)} duplicati interni).")
    return eventi

def scrape_winetourism_lazio(max_eventi=0):
    log_to_gui("🔹 Scraping Winetourism.com – Lazio...")
    driver = setup_driver_persistente()
    url_listato = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
    driver.get(url_listato)
    time.sleep(5)
    listato_soup = BeautifulSoup(driver.page_source, 'html.parser')
    cards = listato_soup.select("div.item-content.ml-3.d-flex.flex-column")

    eventi = []
    seen_links = set()
    for card in cards:
        link_tag = card.select_one('a.item-link')
        if not link_tag:
            continue
        link = link_tag['href']
        if not link.startswith("http"):
            link = "https://www.winetourism.com" + link
        if link in seen_links:
            continue
        seen_links.add(link)
        driver.get(link)
        time.sleep(2)
        dettaglio = BeautifulSoup(driver.page_source, 'html.parser')
        titolo_tag = dettaglio.select_one("h1#experience-title")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": "Lazio, Italia",
            "Prezzo": "Consulta sito",
            "Link": link,
            "Fonte": "Winetourism.com"
        })
    driver.quit()
    log_to_gui(f"✅ Estratti {len(eventi)} eventi unici da Winetourism.com (rimossi {len(cards)-len(eventi)} duplicati interni).")
    return eventi

# --- Logica principale con deduplicazione globale ---
def run_scraping_logic(max_lazio, max_eventbrite, max_wineries, max_winedering, max_winetourism,
                       keyword_filter, min_price_filter, max_price_filter):
    log_to_gui("🚀 Avvio dello script di scraping...")
    all_eventi = []
    all_eventi.extend(scrape_visitlazio(max_lazio))
    all_eventi.extend(scrape_eventbrite(max_eventbrite))
    all_eventi.extend(scrape_wineriesexperience(max_wineries))
    all_eventi.extend(scrape_winedering_latium(max_winedering))
    all_eventi.extend(scrape_winetourism_lazio(max_winetourism))

    if not all_eventi:
        log_to_gui("ℹ️ Nessun evento estratto.")
        return

    df = pd.DataFrame(all_eventi)
    count_before = len(df)
    df.drop_duplicates(subset=["Fonte", "Titolo", "Luogo"], inplace=True)
    count_after = len(df)
    log_to_gui(f"🧹 Rimosse {count_before - count_after} righe duplicate a livello globale.")

    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati_filtrati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati_filtrati.xlsx", index=False)
    log_to_gui(f"✅ Salvati {len(df)} eventi finali in output/")

# --- GUI Tkinter ---
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wine Scraper GUI")
        self.root.geometry("800x750")
        self.create_widgets()
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(input_frame, text="Max eventi per fonte:").grid(row=0, column=0, sticky=tk.W)
        self.max_entries = {}
        for i, fonte in enumerate(["VisitLazio","Eventbrite","WineriesExperience","Winedering","Winetourism"]):
            tk.Label(input_frame, text=fonte+":").grid(row=i+1, column=0, sticky=tk.W)
            e = tk.Entry(input_frame, width=10)
            e.insert(0,"0")
            e.grid(row=i+1, column=1)
            self.max_entries[fonte] = e

        self.scrape_button = tk.Button(input_frame, text="Avvia Scraping", command=self.start_scraping, bg="green", fg="white")
        self.scrape_button.grid(row=7, column=0, pady=10)

        log_frame = tk.Frame(self.root, padx=10, pady=10)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=25, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config('error', foreground='red')

    def start_scraping(self):
        self.scrape_button.config(state=tk.DISABLED)
        max_vals = {fonte:int(e.get()) for fonte,e in self.max_entries.items()}
        threading.Thread(target=run_scraping_logic, args=(
            max_vals["VisitLazio"], max_vals["Eventbrite"], max_vals["WineriesExperience"],
            max_vals["Winedering"], max_vals["Winetourism"], "", None, None
        ), daemon=True).start()

    def process_queue(self):
        while not output_queue.empty():
            msg, is_err = output_queue.get_nowait()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg+"\n", 'error' if is_err else None)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(100, self.process_queue)

if __name__=="__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
