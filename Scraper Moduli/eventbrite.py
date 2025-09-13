import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime
import re

from utils import setup_driver, log_to_gui, salva_parziale

def scrape_eventbrite(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip Eventbrite (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping Eventbrite (versione definitiva)...")
    driver = None
    try:
        driver = setup_driver()
        driver.set_page_load_timeout(180)
        driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
        
        time.sleep(10) 

        log_to_gui("  DEBUG: Inizio fase raccolta link Eventbrite (originale)...")
        elementi = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
        
        all_links = []
        seen_links_set = set()
        for el in elementi:
            link = el.get_attribute("href")
            if link and link not in seen_links_set:
                seen_links_set.add(link)
                all_links.append(link)

        log_to_gui(f"  DEBUG: Raccolti {len(all_links)} link evento dalla pagina di listato.")

        if max_eventi > 0:
            all_links = all_links[:max_eventi]
        
        eventi = []

        for idx, link in enumerate(all_links, start=1):
            titolo_list = "Titolo da listato" 
            
            log_to_gui(f"    DEBUG: Estraggo dati per URL: {link}")

            try:
                driver.get(link)
                time.sleep(3)
            except TimeoutException:
                log_to_gui(f"❌ Timeout caricamento pagina dettaglio Eventbrite: {link}", True)
                continue
            except WebDriverException as e:
                log_to_gui(f"❌ Errore driver su pagina dettaglio Eventbrite {link}: {e}", True)
                continue
            
            event_soup = BeautifulSoup(driver.page_source, 'html.parser')

            # --- ESTRAZIONE TITOLO (Definitiva) ---
            titolo = "Titolo non trovato"
            try:
                titolo_tag = event_soup.find("h1", class_="event-title") # Selettore corretto
                if titolo_tag:
                    titolo = titolo_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Titolo estratto: '{titolo}'")
                else:
                    log_to_gui(f"      DEBUG: Titolo NON trovato con selettore h1.event-title.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Titolo per URL {link}: {e}", is_error=True)


            # --- ESTRAZIONE LUOGO (Definitiva) ---
            luogo = "Consulta sito"
            try:
                luogo_p_tag = event_soup.find("p", class_="location-info__address-text")
                if luogo_p_tag:
                    luogo = luogo_p_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Luogo trovato: '{luogo}' dal tag p.location-info__address-text.")
                else:
                    log_to_gui(f"      DEBUG: Luogo NON trovato con selettore p.location-info__address-text.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Luogo per '{titolo}': {e}", is_error=True)

            if not luogo or luogo == "Consulta sito":
                log_to_gui(f"  ⚠️ Luogo non valorizzato per '{titolo}' (rimane 'Consulta sito')", is_error=False)


            # --- ESTRAZIONE DATA INIZIO/FINE (Definitiva) ---
            data_inizio = "Consulta sito"
            data_fine = "Verifica sul sito"
            
            try:
                start_date_time_tag = event_soup.find("time", class_="start-date")
                if start_date_time_tag and start_date_time_tag.get("datetime"):
                    raw_start_date = start_date_time_tag["datetime"]
                    try:
                        data_inizio = datetime.strptime(raw_start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        data_fine = data_inizio # Se c'è solo start-date, fine è uguale a inizio
                        log_to_gui(f"      DEBUG: Data Inizio trovata e formattata: '{data_inizio}'. Data Fine impostata a Inizio.")
                    except ValueError:
                        log_to_gui(f"      DEBUG: Errore formattazione Data Inizio, uso raw: '{raw_start_date}'.")
                        data_inizio = raw_start_date
                else:
                    log_to_gui(f"      DEBUG: Tag time.start-date NON trovato o datetime assente.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Data Inizio per '{titolo}': {e}", is_error=True)

            if data_inizio == "Consulta sito":
                log_to_gui(f"  ⚠️ Data Inizio non valorizzata per '{titolo}' (rimane 'Consulta sito')", is_error=False)


            # --- ESTRAZIONE ORARIO (Impostato a 'Consulta sito') ---
            orario = "Consulta sito"
            log_to_gui("      DEBUG: Orario gestito come 'Consulta sito' (non trovato un selettore affidabile).")

            # --- ESTRAZIONE PREZZO (Impostato a 'Consulta sito') ---
            prezzo = "Consulta sito"
            log_to_gui("      DEBUG: Prezzo gestito come 'Consulta sito' (troppo complesso/non prioritario).")


            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Attività varie",
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": orario,
                "Luogo": luogo,
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "Eventbrite"
            })
            update_counter("Eventbrite", len(eventi))
            update_total()

            salva_parziale(eventi, "Eventbrite")
            log_to_gui(f"💾 Salvataggio parziale Eventbrite: {len(eventi)} eventi (step {idx})")
            
            driver.back() 
            time.sleep(1)

        return eventi
    except Exception as e:
        log_to_gui(f"❌ Errore critico in scrape_eventbrite: {e}", True)
        return []
    finally:
        if driver:
            driver.quit()
