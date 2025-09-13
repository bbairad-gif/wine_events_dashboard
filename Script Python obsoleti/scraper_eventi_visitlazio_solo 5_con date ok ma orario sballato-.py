import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scrape_visitlazio(max_eventi=5):  # Max 5 per test
    print("🔹 Avvio scraping VisitLazio (orari inclusi)...")
    driver = setup_driver()
    driver.get("https://www.visitlazio.com/web/eventi")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover"))
        )
        time.sleep(2)
    except:
        print("❌ Timeout su VisitLazio")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    event_links = soup.select("a.mec-color-hover")[:max_eventi]

    eventi = []
    for a in event_links:
        titolo = a.get_text(strip=True)
        link = a['href']
        
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')

        raw_start_date = event_soup.find("span", class_="mec-start-date-label")
        raw_end_date = event_soup.find("span", class_="mec-end-date-label")
        raw_times = event_soup.find_all("abbr", class_="mec-events-abbr")
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")

        # Estrarre orari multipli, se presenti
        orari = [abbr.get_text(strip=True) for abbr in raw_times if abbr.get_text(strip=True)]
        final_orario = " – ".join(orari) if orari else ""

        # Pulizia date
        start_date = raw_start_date.get_text(strip=True) if raw_start_date else ""
        end_date = raw_end_date.get_text(strip=True) if raw_end_date else ""

        # Gestione formati strani nelle date
        if "–" in start_date:
            final_start_date = start_date
            final_end_date = ""
        else:
            final_start_date = start_date
            final_end_date = end_date

        eventi.append({
            "Titolo": titolo,
            "Data Inizio": final_start_date,
            "Data Fine": final_end_date,
            "Orario": final_orario,
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (
                luogo_generico.get_text(strip=True) if luogo_generico else ""
            ),
            "Link": link,
            "Fonte": "VisitLazio"
        })
    
    driver.quit()
    return eventi

def main():
    eventi_lazio = scrape_visitlazio(max_eventi=50)  # SOLO 5 PER TEST
    df = pd.DataFrame(eventi_lazio)

    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_visitlazio_test_con_orari.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ Salvati {len(df)} eventi da VisitLazio in 'output/eventi_visitlazio_test_con_orari.csv'")

if __name__ == "__main__":
    main()
