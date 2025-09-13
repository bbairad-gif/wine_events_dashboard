import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def estrai_orari_da_abbr(abbr_list):
    orari = []
    for abbr in abbr_list:
        testo = abbr.get_text(strip=True)
        match = re.findall(r'\d{1,2}:\d{2}', testo)
        if match:
            orari.extend(match)
    return " – ".join(orari) if orari else ""

def estrai_date_da_abbr(abbr_list):
    for abbr in abbr_list:
        testo = abbr.get_text(strip=True)
        # cerca pattern tipo "1 – 3 Agosto 2025"
        match = re.search(r'(\d{1,2}(?:\s?–\s?\d{1,2})?\s+\w+\s+\d{4})', testo)
        if match:
            return match.group(1)
    return ""

def scrape_visitlazio():
    base_url = "https://www.visitlazio.com"
    start_url = "https://www.visitlazio.com/eventi-lazio/"
    eventi = []

    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(start_url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Trova tutti i link agli eventi
    event_links = [a['href'] for a in soup.select("div.mec-event-title a") if a.get('href')]

    for link in event_links:
        event_url = link if link.startswith("http") else base_url + link
        try:
            response = requests.get(event_url, timeout=10)
            event_soup = BeautifulSoup(response.content, "html.parser")

            titolo_tag = event_soup.find("h1", class_="mec-single-title")
            titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza Titolo"

            luogo_tag = event_soup.find("dd", class_="author fn org")
            luogo = luogo_tag.get_text(strip=True) if luogo_tag else ""

            raw_times = event_soup.find_all("abbr", class_="mec-events-abbr")

            final_orario = estrai_orari_da_abbr(raw_times)
            final_start_date = estrai_date_da_abbr(raw_times)
            final_end_date = ""  # opzionale, al momento lasciato vuoto

            eventi.append({
                "Titolo": titolo,
                "Data Inizio": final_start_date,
                "Data Fine": final_end_date,
                "Orario": final_orario,
                "Luogo": luogo,
                "Link": event_url,
                "Fonte": "VisitLazio"
            })

        except Exception as e:
            print(f"Errore con il link {event_url}: {e}")

    driver.quit()

    # Salva su CSV
    with open("eventi_visitlazio.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Titolo", "Data Inizio", "Data Fine", "Orario", "Luogo", "Link", "Fonte"])
        writer.writeheader()
        writer.writerows(eventi)

    print(f"Scraping completato. {len(eventi)} eventi salvati in eventi_visitlazio.csv")

if __name__ == "__main__":
    scrape_visitlazio()
