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
    print("🔹 Scraping VisitLazio...")
    driver = setup_driver()
    driver.get("https://www.visitlazio.com/web/eventi")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover"))
        )
        time.sleep(2)
    except:
        print("❌ Timeout VisitLazio")
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

        orari = [abbr.get_text(strip=True) for abbr in raw_times if abbr.get_text(strip=True)]
        final_orario = " – ".join(orari) if orari else ""

        start_date = raw_start_date.get_text(strip=True) if raw_start_date else ""
        end_date = raw_end_date.get_text(strip=True) if raw_end_date else ""

        if "–" in start_date:
            final_start_date = start_date
            final_end_date = ""
        else:
            final_start_date = start_date
            final_end_date = end_date.lstrip("–").strip() if end_date else ""

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

def scrape_eventbrite():
    print("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italy--lazio/eventi--questa-settimana/")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.eds-event-card-content__primary-content"))
        )
        time.sleep(2)
    except:
        print("❌ Timeout Eventbrite")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    eventi = []

    eventi_divs = soup.select("div.eds-event-card-content__primary-content")
    for div in eventi_divs[:50]:  # Max 50 eventi
        titolo = div.find("div", class_="eds-is-hidden-accessible")
        data = div.find("div", class_="eds-text-bs--fixed eds-text-color--grey-600 eds-l-mar-top-1")
        link = div.find("a", href=True)

        if not (titolo and data and link): continue

        eventi.append({
            "Titolo": titolo.get_text(strip=True),
            "Data Inizio": data.get_text(strip=True),
            "Data Fine": "",
            "Orario": "",
            "Luogo": "Lazio",
            "Link": link['href'],
            "Fonte": "Eventbrite"
        })

    driver.quit()
    return eventi

def main():
    eventi_lazio = scrape_visitlazio(max_eventi=5)
    eventi_eventbrite = scrape_eventbrite()
    all_eventi = eventi_lazio + eventi_eventbrite

    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
