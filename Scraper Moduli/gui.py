import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading # Necessario per gestire il thread di scraping
from utils import output_queue

class ScraperApp:
    def __init__(self, root, start_callback):
        self.root = root
        self.start_callback = start_callback
        self.root.title("Wine Scraper Modular")
        self.root.geometry("950x820")
        self.create_widgets()
        # Intercetta la chiusura della finestra con la 'X'
        self.root.protocol("WM_DELETE_WINDOW", self.chiudi_app)
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(input_frame, text="Max eventi per fonte:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.max_entries = {}
        self.counters = {}
        self.counter_labels = {}
        fonte_list = ["VisitLazio", "Eventbrite", "WineriesExperience", "Winedering", "Winetourism", "ItinerariNelGusto"]

        # Campi di input e contatori
        riga = 1
        for fonte in fonte_list:
            tk.Label(input_frame, text=fonte + ":").grid(row=riga, column=0, sticky=tk.W)
            e = tk.Entry(input_frame, width=6)
            e.insert(0, "0")
            e.grid(row=riga, column=1)
            self.max_entries[fonte] = e
            self.counters[fonte] = 0
            lbl = tk.Label(input_frame, text="0", width=6, anchor="e", font=("Arial", 9, "bold"))
            lbl.grid(row=riga, column=2, sticky=tk.W, padx=5)
            self.counter_labels[fonte] = lbl
            riga += 1

        # Contatore totale (allineato con gli altri contatori)
        tk.Label(input_frame, text="Totale:", font=("Arial", 10, "bold")).grid(row=riga, column=0, sticky=tk.W, pady=(10,0))
        self.total_label = tk.Label(input_frame, text="0", width=6, anchor="e", font=("Arial", 10, "bold"))
        self.total_label.grid(row=riga, column=2, sticky=tk.W, pady=(10,0))

        # Area log
        log_frame = tk.Frame(self.root, padx=10, pady=10)
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=90, height=25, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config('error', foreground='red')

        # Separatore visivo
        separator = tk.Frame(self.root, height=2, bd=1, relief=tk.SUNKEN, bg="#cccccc")
        separator.pack(fill=tk.X, padx=5, pady=8)

        # Barra pulsanti in basso
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack(side=tk.BOTTOM)

        tk.Button(button_frame, text="Disattiva Tutti (-1)", command=self.set_all_minus_one, bg="orange").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Attiva Tutti (0)", command=self.set_all_zero, bg="lightgreen").pack(side=tk.LEFT, padx=5)
        self.scrape_button = tk.Button(button_frame, text="Avvia Scraping", command=self.start_scraping, bg="green", fg="white")
        self.scrape_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Chiudi", command=self.chiudi_app, bg="red", fg="white").pack(side=tk.LEFT, padx=5)

    # Funzioni pulsanti rapidi
    def set_all_minus_one(self):
        for e in self.max_entries.values():
            e.delete(0, tk.END)
            e.insert(0, "-1")
        self.clear_counters() # Azzera i contatori quando si disattiva tutto

    def set_all_zero(self):
        for e in self.max_entries.values():
            e.delete(0, tk.END)
            e.insert(0, "0")
        self.clear_counters() # Azzera i contatori quando si attiva tutto

    def clear_counters(self):
        # Azzera tutti i contatori e il totale
        for fonte in self.counters:
            self.counters[fonte] = 0
            self.counter_labels[fonte].config(text="0")
        self.total_label.config(text="0")
        self.root.update_idletasks()

    # Funzione per confermare uscita
    def chiudi_app(self):
        # Controlla se ci sono thread di scraping attivi
        active_scraping_threads = [t for t in threading.enumerate() if t.is_alive() and t is not threading.current_thread() and t.name != "TkinterQueueProcessor"]
        
        if active_scraping_threads:
            if messagebox.askokcancel("Conferma uscita", "Lo scraping è ancora in corso. Sei sicuro di voler chiudere? Verrà interrotto."):
                # In un'applicazione più complessa, si dovrebbe segnalare ai thread di terminare graziosamente
                self.root.destroy()
        else:
            if messagebox.askokcancel("Conferma uscita", "Sei sicuro di voler chiudere l'applicazione?"):
                self.root.destroy()

    # Callback quando lo scraping è finito
    def on_scraping_finished(self):
        self.scrape_button.config(state=tk.NORMAL) # Riattiva il pulsante Avvia
        if messagebox.askyesno("Fine elaborazione", "Scraping completato!\n\nChiudi l'applicazione?"):
            self.root.destroy()

    # Aggiornamento contatori
    def update_counter(self, fonte, count):
        self.counters[fonte] = count
        self.counter_labels[fonte].config(text=str(count))
        self.update_total()
        self.root.update_idletasks()

    def update_total(self):
        total = sum(self.counters.values())
        self.total_label.config(text=str(total))
        self.root.update_idletasks()

    # Avvio scraping
    def start_scraping(self):
        self.scrape_button.config(state=tk.DISABLED) # Disabilita il pulsante Avvia
        self.clear_counters() # Azzera i contatori all'inizio di un nuovo scraping
        max_vals = {fonte: int(e.get()) for fonte, e in self.max_entries.items()}
        # Passiamo la callback on_scraping_finished al main
        self.start_callback(max_vals, self.update_counter, self.update_total, self.on_scraping_finished)

    # Log output
    def process_queue(self):
        while not output_queue.empty():
            msg, is_err = output_queue.get_nowait()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n", 'error' if is_err else None)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(100, self.process_queue)
