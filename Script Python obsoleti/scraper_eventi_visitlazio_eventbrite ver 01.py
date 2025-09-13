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
    options.add_argument("--headless")  # invisibile
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scrape_visitlazio():
    print("🔹 Avvio scraping VisitLazio...")
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
    driver.quit()
    
    eventi = []
    for a in soup.select("a.mec-color-hover"):
        titolo = a.get_text(strip=True)
        link = a['href']
        parent = a.find_parent()
        data = parent.select_one("span.mec-event-date")
        luogo = parent.select_one("span.mec-event-location")
        eventi.append({
            "Titolo": titolo,
            "Data": data.get_text(strip=True) if data else "",
            "Luogo": luogo.get_text(strip=True) if luogo else "",
            "Link": link,
            "Fonte": "VisitLazio"
        })
    return eventi

def scrape_eventbrite():
    print("🔹 Avvio scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    eventi = []
    for el in links:
        titolo = el.text.strip()
        link = el.get_attribute("href")
        if titolo and link:
            eventi.append({
               "Titolo": titolo,
               "Data": "",
               "Luogo": "",
               "Link": link,
               "Fonte": "Eventbrite"
           
            })
    driver.quit()
    return eventi

def main():
    eventi_lazio = scrape_visitlazio()
    eventi_eventbrite = scrape_eventbrite()
    tutti_eventi = eventi_lazio + eventi_eventbrite
    df = pd.DataFrame(tutti_eventi)
    
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_totali.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ Salvati {len(df)} eventi totali in 'output/eventi_totali.csv'")

if __name__ == "__main__":
    main()
