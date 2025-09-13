import streamlit as st
import pandas as pd
import re # Per la pulizia del prezzo
import os # Per controllare l'esistenza del file

st.set_page_config(page_title="Eventi Vino nel Lazio", layout="wide", initial_sidebar_state="expanded")
st.title("🍷 Eventi Vino e Cultura nel Lazio")
st.markdown("Un elenco aggiornato di degustazioni ed eventi enogastronomici nella regione Lazio.")

# --- Configurazione del percorso del file CSV ---
CSV_PATH = "output/eventi_unificati_filtrati.csv"

# --- Funzione per pulire e convertire il prezzo in numerico ---
@st.cache_data
def clean_price(price_str):
    if isinstance(price_str, str):
        price_str = price_str.lower().replace('from', '').replace('da', '').replace('€', '').strip()
        if '-' in price_str:
            parts = price_str.split('-')
            try:
                return float(parts[0].strip().replace(',', '.'))
            except ValueError:
                pass
        try:
            return float(price_str.replace(',', '.'))
        except ValueError:
            pass
    return None

# --- Caricamento e pre-elaborazione dei dati ---
@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        st.error(f"⚠️ File CSV non trovato: {path}. Assicurati di aver eseguito lo script di scraping.")
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    
    # Pulizia e conversione del prezzo per il filtro
    df['Prezzo_Numerico'] = df['Prezzo'].apply(clean_price)
    
    # Crea i link cliccabili per la visualizzazione
    # Non creiamo più Titolo_Link qui, lo renderemo riga per riga
    # df["Titolo_Link"] = df.apply(lambda row: f"[{row['Titolo']}]({row['Link']})" if row['Link'] and row['Link'] != 'Consulta sito' else row['Titolo'], axis=1)
    
    return df

df_original = load_data(CSV_PATH)

if df_original.empty:
    st.info("Nessun evento disponibile. Esegui lo script di scraping per generare i dati.")
    st.stop()

st.success(f"✅ Caricati {len(df_original)} eventi totali.")

# --- Sidebar per i filtri ---
st.sidebar.header("⚙️ Filtri Eventi")

# Filtro per Fonte (Multi-selezione)
all_sources = df_original["Fonte"].unique().tolist()
selected_sources = st.sidebar.multiselect("Seleziona Fonte:", all_sources, default=all_sources)

# Filtro per Tipologia (Multi-selezione)
all_tipologie = df_original["Tipologia"].unique().tolist()
selected_tipologie = st.sidebar.multiselect("Seleziona Tipologia:", all_tipologie, default=all_tipologie)

# Filtro per Parola Chiave
keyword = st.sidebar.text_input("Cerca per parola chiave (Titolo/Luogo):").strip()

# Filtro per Fascia di Prezzo
with st.sidebar.expander("💰 Filtra per Prezzo"):
    min_price_input_str = st.text_input("Prezzo Minimo (€):", value="").strip()
    max_price_input_str = st.text_input("Prezzo Massimo (€):", value="").strip()

    min_price_filter = float(min_price_input_str) if min_price_input_str else None
    max_price_filter = float(max_price_input_str) if max_price_input_str else None


# --- Applicazione dei filtri ---
df_filtered = df_original.copy()

# Filtro per Fonte
if selected_sources:
    df_filtered = df_filtered[df_filtered["Fonte"].isin(selected_sources)]

# Filtro per Tipologia
if selected_tipologie:
    df_filtered = df_filtered[df_filtered["Tipologia"].isin(selected_tipologie)]

# Filtro per Parola Chiave
if keyword:
    df_filtered = df_filtered[
        df_filtered['Titolo'].astype(str).str.contains(keyword, case=False, na=False) |
        df_filtered['Luogo'].astype(str).str.contains(keyword, case=False, na=False)
    ]

# Filtro per Fascia di Prezzo
price_filter_active = min_price_filter is not None or max_price_filter is not None

if price_filter_active:
    df_filtered = df_filtered[df_filtered['Prezzo_Numerico'].notna()]
    
    if min_price_filter is not None:
        df_filtered = df_filtered[df_filtered['Prezzo_Numerico'] >= min_price_filter]
    if max_price_filter is not None:
        df_filtered = df_filtered[df_filtered['Prezzo_Numerico'] <= max_price_filter]


st.markdown("---")
st.subheader(f"📋 Elenco Eventi Filtrati ({len(df_filtered)} trovati)")

if not df_filtered.empty:
    # ✅ MODIFICA QUI: Visualizzazione riga per riga con st.markdown
    for index, row in df_filtered.iterrows():
        st.markdown(f"**Titolo:** [{row['Titolo']}]({row['Link']})")
        st.markdown(f"**Tipologia:** {row['Tipologia']}")
        st.markdown(f"**Fonte:** {row['Fonte']}")
        st.markdown(f"**Luogo:** {row['Luogo']}")
        st.markdown(f"**Prezzo:** {row['Prezzo']}")
        st.markdown(f"---") # Divisore per ogni evento

    # --- Riepilogo e Download ---
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Eventi Visualizzati", value=len(df_filtered))
    with col2:
        st.download_button(
            label="📥 Scarica CSV Filtrato",
            data=df_filtered.to_csv(index=False, encoding="utf-8-sig"),
            file_name="eventi_lazio_filtrati.csv",
            mime="text/csv",
            help="Scarica solo gli eventi attualmente visualizzati."
        )

    # --- Grafici (Esempio) ---
    st.markdown("---")
    st.subheader("📊 Analisi Rapida")
    
    if not df_filtered["Fonte"].empty:
        source_counts = df_filtered["Fonte"].value_counts()
        if not source_counts.empty:
            st.bar_chart(source_counts)
        else:
            st.info("Nessun dato per il grafico delle fonti con i filtri attuali.")
    
    if not df_filtered["Tipologia"].empty:
        type_counts = df_filtered["Tipologia"].value_counts()
        if not type_counts.empty:
            st.bar_chart(type_counts)
        else:
            st.info("Nessun dato per il grafico delle tipologie con i filtri attuali.")

else:
    st.info("Nessun evento corrisponde ai filtri selezionati.")

st.markdown("---")
st.markdown("App creata con ❤️ da Streamlit. Dati aggiornati dallo scraper.")
