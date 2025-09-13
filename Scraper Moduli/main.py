import threading
import pandas as pd
import os
from gui import ScraperApp
from visitlazio import scrape_visitlazio
from eventbrite import scrape_eventbrite
from wineriesexperience import scrape_wineriesexperience
from winedering import scrape_winedering_latium
from winetourism import scrape_winetourism_lazio
from itinerarinelgusto import scrape_itinerarinelgusto_lazio
from utils import log_to_gui
import tkinter as tk

def run_scraping_logic(max_vals, update_counter, update_total, on_finished_callback):
    all_eventi = []
    scrapers = [
        ("VisitLazio", scrape_visitlazio),
        ("Eventbrite", scrape_eventbrite),
        ("WineriesExperience", scrape_wineriesexperience),
        ("Winedering", scrape_winedering_latium),
        ("Winetourism", scrape_winetourism_lazio),
        ("ItinerariNelGusto", scrape_itinerarinelgusto_lazio)
    ]
    
    log_to_gui("🚀 Avvio dello script di scraping...")
    log_to_gui("--- Configurazione Scrapers ---")
    for fonte, _ in scrapers:
        status = f"Attivo (Max: {max_vals[fonte]})" if max_vals[fonte] != -1 else "Skippato"
        log_to_gui(f"- {fonte}: {status}")
    log_to_gui("-----------------------------")

    for fonte, scraper_func in scrapers:
        if max_vals[fonte] != -1: # Esegue solo se non è skippato
            eventi = scraper_func(max_vals[fonte], update_counter, update_total)
            all_eventi.extend(eventi)
        else:
            # Assicurati che i contatori per gli scraper skippati siano a zero
            update_counter(fonte, 0)
            update_total()


    if not all_eventi:
        log_to_gui("ℹ️ Nessun evento estratto da fonti attive.")
        on_finished_callback() 
        return
    
    df = pd.DataFrame(all_eventi)
    before = len(df)
    df.drop_duplicates(subset=["Fonte", "Titolo", "Luogo"], inplace=True)
    after = len(df)
    log_to_gui(f"🧹 Rimosse {before - after} righe duplicate globali.")
    
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati_filtrati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati_filtrati.xlsx", index=False)
    log_to_gui(f"✅ Salvati {len(df)} eventi finali in output/")
    
    # Report finale per fonte
    log_to_gui("\n--- Riepilogo Estrazioni per Fonte ---")
    for fonte, _ in scrapers:
        count = sum(1 for e in all_eventi if e.get("Fonte") == fonte)
        log_to_gui(f"- {fonte}: {count} eventi")
    log_to_gui(f"Totale eventi finali: {len(df)}")
    log_to_gui("------------------------------------")

    on_finished_callback() # Chiama la callback quando tutto è finito

if __name__=="__main__":
    root = tk.Tk()
    # Rinomina il thread principale per distinguerlo dagli altri thread di scraping
    threading.current_thread().name = "TkinterQueueProcessor" 
    app = ScraperApp(root, lambda max_vals, uc, ut, ofc: threading.Thread(
        target=run_scraping_logic, args=(max_vals, uc, ut, ofc), daemon=True).start())
    root.mainloop()
