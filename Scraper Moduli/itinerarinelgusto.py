import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime
from utils import setup_driver, log_to_gui, salva_parziale

def scrape_itinerarinelgusto_lazio(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip ItinerariNelGusto (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping ItinerariNelGusto – Lazio...")
    driver = setup_driver()
    driver.set_page_load_timeout(180) # Imposta timeout di caricamento pagina a 3 minuti (180 secondi)
    base_url = "https://www.itinerarinelgusto.it"
    initial_list_url = f"{base_url}/sagre-e-feste/lazio"
    
    eventi = []
    seen_event_links = set()
    
    pages_to_visit = [initial_list_url]
    visited_list_urls = set()

    # --- Fase 1: Raccolta URL di tutte le pagine di listato ---
    log_to_gui("  Fase 1: Raccolta URL di tutte le pagine di listato...")
    while pages_to_visit:
        current_list_url = pages_to_visit.pop(0)
        
        if current_list_url in visited_list_urls:
            continue
        visited_list_urls.add(current_list_url)
        
        log_to_gui(f"  Navigazione pagina di listato: {current_list_url}")
        
        try:
            driver.get(current_list_url)
            time.sleep(3)
        except TimeoutException:
            log_to_gui(f"❌ Timeout caricamento pagina di listato: {current_list_url}", True)
            continue
        except WebDriverException as e:
            log_to_gui(f"❌ Errore driver su pagina di listato {current_list_url}: {e}", True)
            continue


        soup = BeautifulSoup(driver.page_source, "html.parser")
        page_container = soup.select_one("p.pages")
        
        if not page_container:
            log_to_gui("  Nessun contenitore di paginazione trovato in questa pagina.")
            break

        all_pagination_links = page_container.find_all("a")
        
        for link_element in all_pagination_links:
            href = link_element.get("href")
            if href:
                full_url = href if href.startswith("http") else base_url + href
                if full_url not in visited_list_urls and full_url not in pages_to_visit:
                    pages_to_visit.append(full_url)
                    log_to_gui(f"  Aggiunto URL paginazione: {full_url}")

    log_to_gui(f"  Fase 1 completata. Trovati {len(visited_list_urls)} URL di listato unici.")
    
    # --- Fase 2: Estrazione eventi da ogni URL di listato scoperto ---
    log_to_gui("  Fase 2: Estrazione eventi da ogni pagina di listato raccolta...")
    
    sorted_list_urls = sorted(list(visited_list_urls), key=lambda x: int(x.split("pg_from=")[-1]) if "pg_from=" in x else 0)

    for list_page_url in sorted_list_urls:
        try:
            driver.get(list_page_url)
            time.sleep(2)
        except TimeoutException:
            log_to_gui(f"❌ Timeout caricamento pagina di listato per estrazione: {list_page_url}", True)
            continue
        except WebDriverException as e:
            log_to_gui(f"❌ Errore driver su pagina di listato per estrazione {list_page_url}: {e}", True)
            continue

        log_to_gui(f"  Estrazione eventi da: {list_page_url}")

        soup_page = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup_page.select("h2.events > a[itemprop='url']")
        
        for a in cards:
            if max_eventi > 0 and len(eventi) >= max_eventi:
                salva_parziale(eventi, "ItinerariNelGusto")
                driver.quit()
                log_to_gui(f"✅ Raggiunto limite {max_eventi} eventi. Scraping ItinerariNelGusto terminato.")
                return eventi
            
            event_detail_href = a.get("href")
            if not event_detail_href.startswith("http"):
                event_detail_href = base_url + event_detail_href
            if event_detail_href in seen_event_links:
                continue
            seen_event_links.add(event_detail_href)
            titolo = a.get_text(strip=True)

            try:
                driver.get(event_detail_href)
                time.sleep(2)
            except TimeoutException:
                log_to_gui(f"❌ Timeout caricamento pagina dettaglio: {event_detail_href}", True)
                driver.back()
                time.sleep(1)
                continue
            except WebDriverException as e:
                log_to_gui(f"❌ Errore driver su pagina dettaglio {event_detail_href}: {e}", True)
                driver.back()
                time.sleep(1)
                continue
            
            det_soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # --- ESTRAZIONE LUOGO ---
            luogo = "Consulta sito"
            try:
                luogo_p_element = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/section/div/div[1]/div[2]/div[1]/div[2]/div[2]/p')
                luogo_strong_element = luogo_p_element.find_element(By.TAG_NAME, 'strong')
                luogo = luogo_strong_element.text.strip()
            except NoSuchElementException:
                log_to_gui(f"  ⚠️ Luogo non trovato per '{titolo}' con XPath fornito (rimane 'Consulta sito')", is_error=False)
            except Exception as e:
                log_to_gui(f"  ❌ Errore generico estrazione Luogo per '{titolo}': {e}", is_error=True)


            # --- ESTRAZIONE DATA INIZIO/FINE ---
            data_inizio = "Consulta sito"
            data_fine = "Consulta sito"
            
            try:
                start_time_element = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/section/div/div[1]/div[2]/div[1]/div[2]/div[1]/p/strong/time[1]')
                data_inizio = start_time_element.text.strip()
            except NoSuchElementException:
                log_to_gui(f"  ⚠️ Data Inizio non trovata per '{titolo}' con XPath fornito (rimane 'Consulta sito')", is_error=False)
            except Exception as e:
                log_to_gui(f"  ❌ Errore generico estrazione Data Inizio per '{titolo}': {e}", is_error=True)

            try:
                end_time_element = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/section/div/div[1]/div[2]/div[1]/div[2]/div[1]/p/strong/time[2]')
                data_fine = end_time_element.text.strip()
            except NoSuchElementException:
                log_to_gui(f"  ⚠️ Data Fine non trovata per '{titolo}' con XPath fornito (rimane 'Consulta sito')", is_error=False)
            except Exception as e:
                log_to_gui(f"  ❌ Errore generico estrazione Data Fine per '{titolo}': {e}", is_error=True)
            
            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Sagra / Festa",
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": "Consulta sito",
                "Luogo": luogo,
                "Prezzo": "Consulta sito",
                "Link": event_detail_href,
                "Fonte": "ItinerariNelGusto"
            })
            update_counter("ItinerariNelGusto", len(eventi))
            update_total()
            
            driver.back() # Torna alla pagina di listato
            time.sleep(1)
        
        salva_parziale(eventi, "ItinerariNelGusto")
        log_to_gui(f"💾 Salvataggio parziale ItinerariNelGusto dopo pagina di listato ({len(eventi)} eventi totali)")

    driver.quit()
    log_to_gui(f"✅ Scraping ItinerariNelGusto completato: {len(eventi)} eventi estratti.")
    return eventi
