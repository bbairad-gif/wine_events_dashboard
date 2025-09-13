import time
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---- Setup Selenium con profilo persistente ----
def setup_driver_persistente():
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Cambia se necessario
    # Browser visibile per completare CAPTCHA
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# ---- Funzione di debug ----
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_winetourism_crop():
    driver = setup_driver_persistente()
    url = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
    driver.get(url)

    print("⚠️ Se appare il CAPTCHA, completalo manualmente ORA.")
    time.sleep(5)  # attesa minima per far apparire eventuale CAPTCHA

    # --- CHIUSURA POPUP COOKIE ---
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All')]"))
        ).click()
        print("✅ Popup cookie chiuso.")
    except:
        print("ℹ️ Nessun popup cookie trovato o già chiuso.")

    time.sleep(2)  # attesa dopo la chiusura del popup

    # Scroll per caricare tutte le schede
    last_height = 0
    while True:
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1)
        new_height = driver.execute_script("return window.scrollY")
        if new_height == last_height:
            break
        last_height = new_height

    # Screenshot intera pagina
    png_data = driver.get_screenshot_as_png()
    driver.quit()

    img = Image.open(io.BytesIO(png_data))
    img.save("screenshot_intero.png")
    print("📂 Salvato: screenshot_intero.png")

    # Crop di test
    width, height = img.size
    crop_top = 300
    crop_bottom = height - 200
    crop_left = 200
    crop_right = width - 200
    img_cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    img_cropped.save("screenshot_croppato.png")
    print("📂 Salvato: screenshot_croppato.png")
