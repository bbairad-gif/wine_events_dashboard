import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime
import re
import locale

from utils import setup_driver, log_to_gui, salva_parziale

# --- Mappatura dei mesi da italiano a inglese per il parsing ---
MONTH_MAPPING = {
    'gennaio': 'January', 'febbraio': 'February', 'marzo': 'March', 'aprile': 'April',
    'maggio': 'May', 'giugno': 'July', 'luglio': 'August', 'settembre': 'September', 'ottobre': 'October', 'novembre': 'November', 'dicembre': 'December'
}

def parse_italian_date_string(date_string):
    """
    Parsa una stringa data in italiano (es. "13 Settembre 2025") e la formatta in dd-mm-yyyy.
    Restituisce None se il parsing fallisce.
    """
    if not date_string:
        return None
    
    cleaned_string = date_string.lower().strip()
    
    for it_month, en_month in MONTH_MAPPING.items():
        cleaned_string = cleaned_string.replace(it_month, en_month)
    
    cleaned_string = re.sub(r'(\d+)(°|º)', r'\1', cleaned_string)

    formats = [
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned_string, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return None


def scrape_visitlazio(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip VisitLazio (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping VisitLazio (esclusione 'Expired!' + parsing Date robusto)...")
    driver = None
    try:
        driver = setup_driver()
        driver.set_page_load_timeout(180)
        driver.get("https://www.visitlazio.com/web/eventi")
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover")))
        time.sleep(2)

        # --- LOGICA PAGINAZIONE "CARICA ALTRO" ---
        log_to_gui("  DEBUG: Inizio fase paginazione 'Carica Altro'...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 50 
        
        while True and scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 

            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                log_to_gui("  DEBUG: Raggiunta la fine dello scroll o nessun nuovo elemento caricato.")
                break
            
            last_height = new_height
            scroll_attempts += 1
            log_to_gui(f"  DEBUG: Scroll pagina: {new_height}px (tentativo {scroll_attempts}/{max_scroll_attempts})")

            temp_soup = BeautifulSoup(driver.page_source, 'html.parser')
            current_event_links = temp_soup.select("a.mec-color-hover")
            if max_eventi > 0 and len(current_event_links) >= max_eventi:
                log_to_gui(f"  DEBUG: Trovati {len(current_event_links)} link, sufficienti per limite {max_eventi}. Stop scroll.")
                break

        log_to_gui(f"  DEBUG: Fase paginazione 'Carica Altro' completata.")

        # --- RACCOLTA LINK DEGLI EVENTI DOPO PAGINAZIONE ---
        soup_final = BeautifulSoup(driver.page_source, 'html.parser')
        all_event_links_elements = soup_final.select("a.mec-color-hover")
        
        if max_eventi > 0:
            all_event_links_elements = all_event_links_elements[:max_eventi] 
        
        seen_links = set()
        eventi = []

        for idx, a_tag in enumerate(all_event_links_elements, start=1):
            titolo_list = a_tag.get_text(strip=True)
            link = a_tag['href']

            if link in seen_links:
                log_to_gui(f"  DEBUG: Link duplicato saltato durante estrazione: {link}", is_error=False)
                continue
            seen_links.add(link)

            titolo = titolo_list

            log_to_gui(f"    DEBUG: Estraggo dati per URL: {link}")

            try:
                driver.get(link)
                time.sleep(3)
            except TimeoutException:
                log_to_gui(f"❌ Timeout caricamento pagina dettaglio VisitLazio: {link}", True)
                continue
            except WebDriverException as e:
                log_to_gui(f"❌ Errore driver su pagina dettaglio VisitLazio {link}: {e}", True)
                continue
            
            event_soup = BeautifulSoup(driver.page_source, 'html.parser')

            # --- VERIFICA STATO "EXPIRED!" ---
            expired_span = event_soup.find("span", class_="mec-holding-status-expired")
            if expired_span:
                log_to_gui(f"      DEBUG: Trovato stato 'Expired!' per '{titolo}'. Evento scartato.", is_error=False)
                salva_parziale(eventi, "VisitLazio") 
                continue

            # --- ESTRAZIONE TITOLO (dal tag h1 della pagina di dettaglio, più preciso) ---
            titolo_tag = event_soup.find("h1", class_="entry-title")
            if titolo_tag:
                titolo = titolo_tag.get_text(strip=True)
                log_to_gui(f"      DEBUG: Titolo estratto dalla pagina dettaglio: '{titolo}'")
            else:
                log_to_gui(f"      DEBUG: Titolo NON trovato con selettore h1.entry-title. Uso titolo da listato.")

            # --- ESTRAZIONE LUOGO (Funzionante) ---
            luogo = "Consulta sito"
            try:
                luogo_dd_tag = event_soup.find("dd", class_="author fn org")
                if luogo_dd_tag:
                    luogo = luogo_dd_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Luogo trovato: '{luogo}' dal tag dd.author.fn.org")
                else:
                    log_to_gui(f"      DEBUG: Luogo NON trovato con selettore dd.author.fn.org.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Luogo per '{titolo}': {e}", is_error=True)


            if not luogo or luogo == "Consulta sito":
                log_to_gui(f"  ⚠️ Luogo non valorizzato per '{titolo}' (rimane 'Consulta sito')", is_error=False)

            # --- ESTRAZIONE DATA INIZIO/FINE (Logica parsing robusta) ---
            data_inizio = "Consulta sito"
            data_fine = "Verifica sul sito"
            
            try:
                date_span_tag = event_soup.find("span", class_="mec-start-date-label")
                if date_span_tag:
                    full_date_string = date_span_tag.get_text(strip=True)
                    log_to_gui(f"      DEBUG: Stringa data completa trovata: '{full_date_string}'")

                    if " – " in full_date_string: # Range di date
                        parts = full_date_string.split(" – ")
                        if len(parts) == 2:
                            start_day_raw = parts[0].strip()
                            end_part_raw = parts[1].strip()
                            
                            anno_match = re.search(r'\d{4}', end_part_raw)
                            anno = anno_match.group(0) if anno_match else str(datetime.now().year)
                            
                            month_match = re.search(r'[A-Za-z]+', end_part_raw) 
                            mese_seconda_parte = month_match.group(0) if month_match else ""

                            start_part_with_month_year = f"{start_day_raw} {mese_seconda_parte} {anno}"
                            
                            data_inizio = parse_italian_date_string(start_part_with_month_year)
                            data_fine = parse_italian_date_string(end_part_raw)
                            
                            if data_inizio and data_fine:
                                log_to_gui(f"      DEBUG: Date range parsate: Inizio='{data_inizio}', Fine='{data_fine}'")
                            else:
                                log_to_gui(f"      DEBUG: Errore parsing date range, una o entrambe le date sono None.")
                                data_inizio = full_date_string
                                data_fine = "Verifica sul sito"
                        else:
                            log_to_gui(f"      DEBUG: Stringa range data non splittabile correttamente: '{full_date_string}'")
                            data_inizio = full_date_string
                            data_fine = "Verifica sul sito"
                    else: # Singola data
                        data_inizio = parse_italian_date_string(full_date_string)
                        if data_inizio:
                            data_fine = "Verifica sul sito"
                            log_to_gui(f"      DEBUG: Data singola parsata: Inizio='{data_inizio}', Fine='{data_fine}'")
                        else:
                            log_to_gui(f"      DEBUG: Errore parsing data singola, uso raw string.")
                            data_inizio = full_date_string
                            data_fine = "Verifica sul sito"
                else:
                    log_to_gui(f"      DEBUG: Span '.mec-start-date-label' per date NON trovato.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Date per '{titolo}': {e}", is_error=True)

            # ⚠️ CORREZIONE QUI: L'avviso deve essere solo se data_inizio è "Consulta sito"
            if data_inizio == "Consulta sito":
                log_to_gui(f"  ⚠️ Data Inizio non valorizzata per '{titolo}' (rimane 'Consulta sito')", is_error=False)


            # --- ESTRAZIONE ORARIO (Funzionante) ---
            orario = "Consulta sito"
            try:
                orario_dl_tag = event_soup.find("div", class_="mec-single-event-time")
                if orario_dl_tag:
                    orario_abbr_tag = orario_dl_tag.find("abbr", class_="mec-events-abbr")
                    if orario_abbr_tag:
                        orario = orario_abbr_tag.get_text(strip=True)
                        log_to_gui(f"      DEBUG: Orario trovato: '{orario}'")
                    else:
                        log_to_gui(f"      DEBUG: Abbr per orario NON trovato.")
                else:
                    log_to_gui(f"      DEBUG: Div mec-single-event-time per orario NON trovato.")
            except Exception as e:
                log_to_gui(f"      ❌ Errore estrazione Orario per '{titolo}': {e}", is_error=True)


            # --- ESTRAZIONE PREZZO (Gestito come non presente) ---
            prezzo = "Consulta sito"
            log_to_gui("      DEBUG: Prezzo gestito come 'Consulta sito' (non presente di solito).")


            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Attività varie",
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": orario,
                "Luogo": luogo,
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "VisitLazio"
            })
            update_counter("VisitLazio", len(eventi))
            update_total()

            salva_parziale(eventi, "VisitLazio")
            log_to_gui(f"💾 Salvataggio parziale VisitLazio: {len(eventi)} eventi (step {idx})")
            
            driver.back() 
            time.sleep(1)

        return eventi
    except Exception as e:
        log_to_gui(f"❌ Errore critico in scrape_visitlazio: {e}", True)
        return []
    finally:
        if driver:
            driver.quit()
