import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime
import re

from utils import setup_driver_persistente, log_to_gui, salva_parziale

def scrape_winetourism_lazio(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip Winetourism (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping Winetourism.com – Lazio (estrazione Luogo e Prezzo precisa)...")
    driver = None
    try:
        driver = setup_driver_persistente() # Usa il driver persistente
        driver.set_page_load_timeout(180)
        url_listato = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
        driver.get(url_listato)
        time.sleep(5)

        # Eventuali popup cookie o altri elementi iniziali (se presenti)
        # try:
        #     accept_button = WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All')]"))
        #     )
        #     accept_button.click()
        #     log_to_gui("  DEBUG: Popup cookie 'Accept All' chiuso.")
        # except:
        #     log_to_gui("  DEBUG: Nessun popup cookie 'Accept All' trovato o già chiuso.")
        # time.sleep(2) 

        # --- LOGICA PAGINAZIONE WINETOURISM (scroll infinito) ---
        log_to_gui("  DEBUG: Inizio fase paginazione Winetourism (scrolling infinito)...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 50 
        
        while True and scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) # Attende il caricamento di nuovi elementi

            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                log_to_gui("  DEBUG: Raggiunta la fine dello scroll o nessun nuovo elemento caricato.")
                break
            
            last_height = new_height
            scroll_attempts += 1
            log_to_gui(f"  DEBUG: Scroll pagina: {new_height}px (tentativo {scroll_attempts}/{max_scroll_attempts})")

            temp_soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Selettore per le card degli eventi
            current_event_cards = temp_soup.select("div.item-content.ml-3.d-flex.flex-column")
            if max_eventi > 0 and len(current_event_cards) >= max_eventi:
                log_to_gui(f"  DEBUG: Trovate {len(current_event_cards)} card, sufficienti per limite {max_eventi}. Stop scroll.")
                break
        
        log_to_gui(f"  DEBUG: Fase paginazione Winetourism completata.")


        # --- RACCOLTA LINK DEGLI EVENTI DOPO PAGINAZIONE ---
        soup_final = BeautifulSoup(driver.page_source, 'html.parser')
        all_event_cards_elements = soup_final.select("div.item-content.ml-3.d-flex.flex-column")
        
        all_links = []
        seen_links_set = set()
        for card in all_event_cards_elements:
            link_tag = card.select_one('a.item-link')
            if link_tag and link_tag.get("href"):
                link = link_tag["href"]
                if not link.startswith("http"):
                    link = "https://www.winetourism.com" + link
                if link not in seen_links_set:
                    seen_links_set.add(link)
                    all_links.append(link)

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
                log_to_gui(f"❌ Timeout caricamento pagina dettaglio Winetourism: {link}", True)
                continue
            except WebDriverException as e:
                log_to_gui(f"❌ Errore driver su pagina dettaglio Winetourism {link}: {e}", True)
                continue
            
            event_soup = BeautifulSoup(driver.page_source, 'html.parser')

            # --- ESTRAZIONE TITOLO (dal tag h1 della pagina di dettaglio) ---
            titolo = "Titolo non trovato"
            try:
                titolo_tag = event_soup.find("h1", id="experience-title") # Selettore comune Winetourism
                if titolo_tag:
                    titolo = titolo_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Titolo estratto: '{titolo}'")
                else:
                    log_to_gui(f"      DEBUG: Titolo NON trovato con selettore h1#experience-title.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Titolo per URL {link}: {e}", is_error=True)


            # --- ESTRAZIONE LUOGO (Definitiva e precisa) ---
            luogo = "Consulta sito"
            try:
                luogo_span_tag = event_soup.find("span", class_="font-size-2 font-weight-medium margin-left-small")
                if luogo_span_tag:
                    luogo = luogo_span_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Luogo trovato: '{luogo}' dal tag span.font-size-2...")
                else:
                    log_to_gui(f"      DEBUG: Luogo NON trovato con selettore span.font-size-2...")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Luogo per '{titolo}': {e}", is_error=True)

            if not luogo or luogo == "Consulta sito":
                log_to_gui(f"  ⚠️ Luogo non valorizzato per '{titolo}' (rimane 'Consulta sito')", is_error=False)


            # --- ESTRAZIONE DATA INIZIO/FINE (Lasciato come "Consulta sito" / "Prenotare") ---
            data_inizio = "Prenotare"
            data_fine = "Prenotare"
            log_to_gui("      DEBUG: Date gestite come 'Prenotare' (come richiesto).")

            # --- ESTRAZIONE ORARIO (Lasciato come "Consulta sito") ---
            orario = "Consulta sito"
            log_to_gui("      DEBUG: Orario gestito come 'Consulta sito' (come richiesto).")

            # --- ESTRAZIONE PREZZO (Definitiva e precisa) ---
            prezzo = "Consulta sito"
            try:
                prezzo_span_tag = event_soup.find("span", class_="text-large font-weight-medium")
                if prezzo_span_tag:
                    prezzo_raw = prezzo_span_tag.get_text(strip=True)
                    prezzo = prezzo_raw.replace("€", "").strip() # Rimuovi solo il simbolo dell'euro
                    log_to_gui(f"      DEBUG: Prezzo trovato: '{prezzo_raw}' -> pulito: '{prezzo}'")
                else:
                    log_to_gui(f"      DEBUG: Prezzo NON trovato con selettore specifico.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Prezzo per '{titolo}': {e}", is_error=True)


            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Degustazione", # Tipologia più specifica per Winetourism
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": orario,
                "Luogo": luogo,
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "Winetourism.com"
            })
            update_counter("Winetourism", len(eventi))
            update_total()

            salva_parziale(eventi, "Winetourism.com")
            log_to_gui(f"💾 Salvataggio parziale Winetourism.com: {len(eventi)} eventi (step {idx})")
            
            driver.back() 
            time.sleep(1)

        return eventi
    except Exception as e:
        log_to_gui(f"❌ Errore critico in scrape_winetourism_lazio: {e}", True)
        return []
    finally:
        if driver:
            driver.quit()
