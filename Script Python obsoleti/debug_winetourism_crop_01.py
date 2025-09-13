import os
import time
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---- Setup Selenium con profilo persistente ----
def setup_driver_persistente():
    options = Options()
    # Assicurati che questo percorso sia corretto per la tua installazione di Chrome
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # User-Agent reale
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

    # Cartella per il profilo persistente (cookie + cache)
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")

    # Imposta una dimensione finestra grande per catturare più contenuto in uno screenshot
    options.add_argument("--window-size=1920,3000") # Larghezza, Altezza

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ---- Funzione di debug ----
def debug_winetourism_crop():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output")
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 I file di debug verranno salvati in: {output_dir}")

    driver = None # Inizializza driver a None per il blocco finally
    try:
        driver = setup_driver_persistente()
        url = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
        driver.get(url)
        print(f"🌐 Aperta la pagina: {url}")

        print("⚠️ Se appare il CAPTCHA di Cloudflare, completalo manualmente ORA.")
        time.sleep(10)  # attesa per far apparire eventuale CAPTCHA/popup cookie

        # --- CHIUSURA POPUP COOKIE ---
        try:
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All')]"))
            )
            accept_button.click()
            print("✅ Popup cookie 'Accept All' chiuso.")
        except:
            try:
                decline_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Decline All')]"))
                )
                decline_button.click()
                print("✅ Popup cookie 'Decline All' chiuso.")
            except:
                print("ℹ️ Nessun popup cookie trovato o già chiuso.")

        time.sleep(3)  # Attesa dopo la chiusura del popup per stabilizzazione pagina

        # Scroll per caricare tutte le schede (scroll infinito)
        print("⏬ Inizio scroll infinito per caricare tutti i contenuti...")
        last_height = 0
        scroll_attempts = 0
        max_scroll_attempts = 15 # Aumentato per siti con molti contenuti
        
        while True and scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);") # Scrolla di 800px alla volta
            time.sleep(2) # Attesa per il caricamento dei nuovi contenuti
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("⬆️ Raggiunta la fine dello scroll o nessun nuovo contenuto caricato.")
                break
            last_height = new_height
            scroll_attempts += 1
            print(f"   Scroll: {new_height}px (tentativo {scroll_attempts}/{max_scroll_attempts})")

        print("📸 Acquisizione screenshot intero della pagina...")
        png_data = driver.get_screenshot_as_png()
        print(f"📏 Dimensione screenshot grezzo: {len(png_data)} byte")

        if len(png_data) > 1000: # Se il PNG non è praticamente vuoto
            img = Image.open(io.BytesIO(png_data))
            screenshot_path = os.path.join(output_dir, "screenshot_intero.png")
            img.save(screenshot_path)
            print(f"✅ Salvato: {screenshot_path}")

            # --- Valori di crop AGGIORNATI per il debug ---
            width, height = img.size
            crop_top = 280
            crop_bottom = height - 100
            crop_left = 120
            crop_right = width - 120

            # Assicurati che le coordinate di crop siano valide
            crop_left = max(0, min(crop_left, width - 1))
            crop_top = max(0, min(crop_top, height - 1))
            crop_right = max(crop_left + 1, min(crop_right, width))
            crop_bottom = max(crop_top + 1, min(crop_bottom, height))

            if crop_right > crop_left and crop_bottom > crop_top:
                img_cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                cropped_path = os.path.join(output_dir, "screenshot_croppato.png")
                img_cropped.save(cropped_path)
                print(f"✅ Salvato: {cropped_path}")
            else:
                print(f"❌ Le dimensioni del crop non sono valide: left={crop_left}, top={crop_top}, right={crop_right}, bottom={crop_bottom}. Non è stato salvato nessun screenshot croppato.")
        else:
            print("❌ Lo screenshot acquisito è vuoto o troppo piccolo. La pagina potrebbe non aver caricato il contenuto.")

    except Exception as e:
        print(f"❌ FATAL ERROR: Si è verificato un errore durante il debug: {e}")
        # Salva uno screenshot in caso di errore per vedere lo stato della pagina
        if driver:
            error_screenshot_path = os.path.join(output_dir, "error_page_screenshot.png")
            driver.save_screenshot(error_screenshot_path)
            print(f"📂 Salvato screenshot della pagina all'errore: {error_screenshot_path}")
    finally:
        if driver:
            driver.quit()
            print("Browser chiuso.")

if __name__ == "__main__":
    debug_winetourism_crop()
