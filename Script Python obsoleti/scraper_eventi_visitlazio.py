from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

service = Service("C:\\wine_scraper\\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://www.visitlazio.com/web/eventi"
driver.get(url)

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover"))
    )
    time.sleep(2)
except:
    print("⚠️ Timeout: eventi non caricati")
    driver.quit()
    exit()

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, 'html.parser')

eventi = []
for a in soup.select("a.mec-color-hover"):
    titolo = a.get_text(strip=True)
    link = a['href']
    
    # Cerco fratelli con info di data e luogo (modifica se necessario)
    parent = a.find_parent()
    data = parent.select_one("span.mec-event-date")
    luogo = parent.select_one("span.mec-event-location")

    eventi.append({
        "Titolo": titolo,
        "Data": data.get_text(strip=True) if data else "",
        "Luogo": luogo.get_text(strip=True) if luogo else "",
        "Link": link
    })

# Salvo CSV
with open("eventi_visitlazio.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Titolo", "Data", "Luogo", "Link"])
    writer.writeheader()
    writer.writerows(eventi)

print(f"✅ Salvati {len(eventi)} eventi")
