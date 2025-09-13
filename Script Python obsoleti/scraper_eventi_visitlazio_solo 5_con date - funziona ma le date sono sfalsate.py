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

def scrape_visitlazio(max_eventi=5):
    print("🔹 Avvio scraping VisitLazio (5 eventi con data, ora, luogo)...")
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
        
        # Vai sul singolo evento per leggere le info dettagliate
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        start_date = event_soup.find("span", class_="mec-start-date-label")
        end_date = event_soup.find("span", class_="mec-end-date-label")
        orario = event_soup.find("abbr", class_="mec-events-abbr")
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")

        eventi.append({
            "Titolo": titolo,
            "Data Inizio": start_date.get_text(strip=True) if start_date else "",
            "Data Fine": end_date.get_text(strip=True) if end_date else "",
            "Orario": orario.get_text(strip=True) if orario else "",
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (
                luogo_generico.get_text(strip=True) if luogo_generico else ""
            ),
            "Link": link,
            "Fonte": "VisitLazio"
        })
    
    driver.quit()
    return eventi

def main():
    eventi_lazio = scrape_visitlazio(max_eventi=5)
    df = pd.DataFrame(eventi_lazio)
    
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_visitlazio_con_date_orario_luogo.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ Salvati {len(df)} eventi da VisitLazio in 'output/eventi_visitlazio_con_date_orario_luogo.csv'")

if __name__ == "__main__":
    main()
