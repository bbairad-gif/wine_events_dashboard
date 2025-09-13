import queue
import os
import pandas as pd
from datetime import datetime

# Coda globale per inviare messaggi alla GUI
output_queue = queue.Queue()

def log_to_gui(message, is_error=False):
    """
    Invia un messaggio di log alla GUI.
    message: stringa del messaggio
    is_error: True se il messaggio è di errore, False altrimenti
    """
    output_queue.put((message, is_error))

def setup_driver(headless=True):
    """
    Driver Selenium per scraping normale.
    headless=True: avvia Chrome in modalità invisibile
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def setup_driver_persistente():
    """
    Driver Selenium persistente (mantiene cookie/profilo) per siti con protezioni.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--user-agent=Mozilla/5.0")
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")
    options.add_argument("--window-size=1920,3000")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def salva_parziale(eventi, nome_fonte):
    """
    Salva un file CSV/Excel parziale con gli eventi raccolti finora.
    eventi: lista di dizionari con i dati
    nome_fonte: nome dello scraper (es. 'VisitLazio')
    """
    if not eventi:
        return
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(eventi)
    csv_path = f"output/eventi_unificati_parziale_{nome_fonte}.csv"
    excel_path = f"output/eventi_unificati_parziale_{nome_fonte}.xlsx"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(excel_path, index=False)

    # Messaggio di log automatico
    log_to_gui(f"💾 Salvataggio parziale {nome_fonte}: {len(eventi)} eventi")
