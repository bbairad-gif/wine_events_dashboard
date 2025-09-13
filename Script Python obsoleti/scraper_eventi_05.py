import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import os
import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- Coda per log GUI ---
output_queue = queue.Queue()
def log_to_gui(message, is_error=False):
    output_queue.put((message, is_error))

# --- Selenium Drivers ---
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

# --- SCRAPERS ---
def scrape_visitlazio(max_eventi, update_counter, update_total):
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
        time.sleep(1)
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Attività varie",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": "Consulta sito",
            "Prezzo": "Consulta sito",
            "Link": link,
            "Fonte": "VisitLazio"
        })
        update_counter("VisitLazio", len(eventi))
        update_total()
    driver.quit()
    return eventi

def scrape_eventbrite(max_eventi, update_counter, update_total):
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
            update_counter("Eventbrite", len(eventi))
            update_total()
        except:
            continue
    driver.quit()
    return eventi

def scrape_wineriesexperience(max_eventi, update_counter, update_total):
    log_to_gui("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    base_url = "https://wineriesexperience.it"
    driver.get(f"{base_url}/collections/degustazioni-vini-lazio")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = [base_url + a['href'] for a in soup.select("a.product-grid-item--link")]
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
        prezzo = prezzo_tag.text.strip() if prezzo_tag else "Consulta sito"
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
        update_counter("WineriesExperience", len(eventi))
        update_total()
    driver.quit()
    return eventi

def scrape_winedering_latium(max_eventi, update_counter, update_total):
    log_to_gui("🔹 Scraping Winedering Lazio...")
    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        log_to_gui(f"❌ Errore HTTP: {resp.status_code}", True)
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
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
        update_counter("Winedering", len(eventi))
        update_total()
    return eventi

def scrape_winetourism_lazio(max_eventi, update_counter, update_total):
    log_to_gui("🔹 Scraping Winetourism.com – Lazio...")
    driver = setup_driver_persistente()
    url_listato = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
    driver.get(url_listato)
    time.sleep(5)
    cards = BeautifulSoup(driver.page_source, 'html.parser').select("div.item-content.ml-3.d-flex.flex-column")
    eventi = []
    seen_links = set()
    for card in cards:
        if max_eventi > 0 and len(eventi) >= max_eventi:
            break
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
        titolo_tag = BeautifulSoup(driver.page_source, 'html.parser').select_one("h1#experience-title")
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
        update_counter("Winetourism", len(eventi))
        update_total()
    driver.quit()
    return eventi

def scrape_itinerarinelgusto_lazio(max_eventi, update_counter, update_total):
    log_to_gui("🔹 Scraping ItinerariNelGusto – Lazio con paginazione a blocchi...")
    driver = setup_driver()
    driver.get("https://www.itinerarinelgusto.it/sagre-e-feste/lazio")
    time.sleep(2)

    eventi = []
    seen_links = set()

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        page_container = soup.select_one("p.pages")
        if not page_container:
            break
        page_links = page_container.find_all("a")
        
        numeric_links = [a for a in page_links if a.text.strip().isdigit()]
        arrow_links = [a for a in page_links if "arrows" in a.get("class", [])]

        for num_link in numeric_links:
            page_num = num_link.text.strip()
            try:
                btn = driver.find_element(By.LINK_TEXT, page_num)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
            except:
                continue

            soup_page = BeautifulSoup(driver.page_source, "html.parser")
            cards = soup_page.select("h2.events > a[itemprop='url']")
            for a in cards:
                if max_eventi > 0 and len(eventi) >= max_eventi:
                    driver.quit()
                    return eventi
                link = a.get("href")
                if not link.startswith("http"):
                    link = "https://www.itinerarinelgusto.it" + link
                if link in seen_links:
                    continue
                seen_links.add(link)
                titolo = a.get_text(strip=True)

                driver.get(link)
                time.sleep(1)
                det_soup = BeautifulSoup(driver.page_source, "html.parser")
                luogo = ""
                luogo_tag = det_soup.find("ion-icon", {"name": "location"})
                if luogo_tag and luogo_tag.parent:
                    luogo = luogo_tag.parent.get_text(strip=True)
                data_inizio = "Consulta sito"
                data_fine = "Consulta sito"
                date_div = det_soup.select_one("div.property.eventi-date.date")
                if date_div:
                    start_meta = date_div.find("meta", {"itemprop": "startDate"})
                    end_meta = date_div.find("meta", {"itemprop": "endDate"})
                    if start_meta and start_meta.get("content"):
                        data_inizio = start_meta["content"].split("T")[0]
                    if end_meta and end_meta.get("content"):
                        data_fine = end_meta["content"].split("T")[0]
                eventi.append({
                    "Titolo": titolo,
                    "Tipologia": "Sagra / Festa",
                    "Data Inizio": data_inizio,
                    "Data Fine": data_fine,
                    "Orario": "Consulta sito",
                    "Luogo": luogo,
                    "Prezzo": "Consulta sito",
                    "Link": link,
                    "Fonte": "ItinerariNelGusto"
                })
                update_counter("ItinerariNelGusto", len(eventi))
                update_total()
                driver.back()
                time.sleep(1)

        if arrow_links:
            try:
                next_block_btn = driver.find_element(By.XPATH, "//a[@class='arrows']")
                driver.execute_script("arguments[0].click();", next_block_btn)
                time.sleep(2)
            except:
                break
        else:
            break

    driver.quit()
    return eventi

# --- LOGICA PRINCIPALE ---
def run_scraping_logic(max_vals, update_counter, update_total):
    all_eventi = []
    all_eventi.extend(scrape_visitlazio(max_vals["VisitLazio"], update_counter, update_total))
    all_eventi.extend(scrape_eventbrite(max_vals["Eventbrite"], update_counter, update_total))
    all_eventi.extend(scrape_wineriesexperience(max_vals["WineriesExperience"], update_counter, update_total))
    all_eventi.extend(scrape_winedering_latium(max_vals["Winedering"], update_counter, update_total))
    all_eventi.extend(scrape_winetourism_lazio(max_vals["Winetourism"], update_counter, update_total))
    all_eventi.extend(scrape_itinerarinelgusto_lazio(max_vals["ItinerariNelGusto"], update_counter, update_total))
    if not all_eventi:
        log_to_gui("ℹ️ Nessun evento estratto.")
        return
    df = pd.DataFrame(all_eventi)
    before = len(df)
    df.drop_duplicates(subset=["Fonte", "Titolo", "Luogo"], inplace=True)
    after = len(df)
    log_to_gui(f"🧹 Rimosse {before - after} righe duplicate globali.")
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati_filtrati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati_filtrati.xlsx", index=False)
    log_to_gui(f"✅ Salvati {len(df)} eventi finali in output/")

# --- GUI ---
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wine Scraper GUI con Contatori Live e Totale")
        self.root.geometry("900x780")
        self.create_widgets()
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(input_frame, text="Max eventi per fonte:").grid(row=0, column=0, sticky=tk.W)
        self.max_entries = {}
        self.counters = {}
        self.counter_labels = {}
        font_bold = ("Arial", 9, "bold")
        riga = 1
        for fonte in ["VisitLazio","Eventbrite","WineriesExperience","Winedering","Winetourism","ItinerariNelGusto"]:
            tk.Label(input_frame, text=fonte+":").grid(row=riga, column=0, sticky=tk.W)
            e = tk.Entry(input_frame, width=6)
            e.insert(0,"0")
            e.grid(row=riga, column=1)
            self.max_entries[fonte] = e
            self.counters[fonte] = 0
            lbl = tk.Label(input_frame, text="0", width=6, anchor="e", font=font_bold)
            lbl.grid(row=riga, column=2, sticky=tk.W, padx=5)
            self.counter_labels[fonte] = lbl
            riga += 1
        # Contatore totale
        tk.Label(input_frame, text="Totale:", font=("Arial", 10, "bold")).grid(row=riga, column=0, sticky=tk.W, pady=(10,0))
        self.total_label = tk.Label(input_frame, text="0", width=6, anchor="e", font=("Arial", 10, "bold"))
        self.total_label.grid(row=riga, column=1, sticky=tk.W, pady=(10,0))
        self.scrape_button = tk.Button(input_frame, text="Avvia Scraping", command=self.start_scraping, bg="green", fg="white")
        self.scrape_button.grid(row=riga+1, column=0, pady=10)
        log_frame = tk.Frame(self.root, padx=10, pady=10)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=25, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config('error', foreground='red')

    def update_counter(self, fonte, count):
        self.counters[fonte] = count
        self.counter_labels[fonte].config(text=str(count))
        self.root.update_idletasks()

    def update_total(self):
        total = sum(self.counters.values())
        self.total_label.config(text=str(total))
        self.root.update_idletasks()

    def start_scraping(self):
        self.scrape_button.config(state=tk.DISABLED)
        max_vals = {fonte:int(e.get()) for fonte,e in self.max_entries.items()}
        threading.Thread(target=run_scraping_logic, args=(max_vals, self.update_counter, self.update_total), daemon=True).start()

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
