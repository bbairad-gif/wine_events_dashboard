import streamlit as st
import pandas as pd
import re 
import os 

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="Eventi Vino nel Lazio", layout="wide", initial_sidebar_state="collapsed") 
st.title("🍷 Eventi Vino e Cultura nel Lazio")
st.markdown("Un elenco aggiornato di degustazioni ed eventi enogastronomici nella regione Lazio.")

CSV_PATH = "output/eventi_unificati_filtrati.csv"

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

@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        st.error(f"⚠️ File CSV non trovato: {path}. Assicurati di aver eseguito lo script di scraping.")
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    # Trova una colonna simile a "Prezzo"
    prezzo_col = None
    for col in df.columns:
        if col.strip().lower() in ["prezzo", "costo", "price"]:
            prezzo_col = col
            break

    # Se la colonna esiste, calcola Prezzo_Numerico
    if prezzo_col:
        df["Prezzo_Numerico"] = df[prezzo_col].apply(clean_price)
    else:
        st.warning("⚠️ Nessuna colonna 'Prezzo' trovata nel CSV. Filtri prezzo disattivati.")
        df["Prezzo_Numerico"] = None

    df.replace("consulta sito", "Consulta sito", inplace=True)
    df.replace("Senza titolo (dettaglio)", "Senza titolo", inplace=True) 
    
    return df

df_original = load_data(CSV_PATH)

if df_original.empty:
    st.info("Nessun evento disponibile. Esegui lo script di scraping per generare i dati.")
    st.stop()

st.success(f"✅ Caricati {len(df_original)} eventi totali.")

st.markdown("---")
st.subheader("⚙️ Filtra i Risultati")

col_filter1, col_filter2, col_filter3 = st.columns([0.3, 0.25, 0.45]) 

with col_filter1:
    all_sources = df_original["Fonte"].unique().tolist() if "Fonte" in df_original.columns else []
    selected_sources = st.multiselect("Seleziona Fonte:", all_sources, default=all_sources)

with col_filter2:
    all_tipologie = df_original["Tipologia"].unique().tolist() if "Tipologia" in df_original.columns else []
    selected_tipologie = st.multiselect("Seleziona Tipologia:", all_tipologie, default=all_tipologie)

with col_filter3:
    keyword = st.text_input("Cerca per parola chiave (Titolo/Luogo):").strip()

# Sidebar prezzo solo se disponibile
if df_original["Prezzo_Numerico"].notna().any():
    st.sidebar.header("💰 Filtri Prezzo") 
    price_col = df_original['Prezzo_Numerico'].dropna()
    min_price_default = float(price_col.min()) if not price_col.empty else 0.0
    max_price_default = float(price_col.max()) if not price_col.empty else 1000.0

    min_price_input_str = st.sidebar.text_input("Prezzo Minimo (€):", value="").strip()
    max_price_input_str = st.sidebar.text_input("Prezzo Massimo (€):", value="").strip()

    min_price_filter = float(min_price_input_str) if min_price_input_str else None
    max_price_filter = float(max_price_input_str) if max_price_input_str else None
else:
    min_price_filter = max_price_filter = None

df_filtered = df_original.copy()

if selected_sources:
    df_filtered = df_filtered[df_filtered["Fonte"].isin(selected_sources)]

if selected_tipologie:
    df_filtered = df_filtered[df_filtered["Tipologia"].isin(selected_tipologie)]

if keyword:
    df_filtered = df_filtered[
        df_filtered['Titolo'].astype(str).str.contains(keyword, case=False, na=False) |
        df_filtered['Luogo'].astype(str).str.contains(keyword, case=False, na=False)
    ]

if min_price_filter is not None or max_price_filter is not None:
    df_filtered = df_filtered[df_filtered['Prezzo_Numerico'].notna()]
    if min_price_filter is not None:
        df_filtered = df_filtered[df_filtered['Prezzo_Numerico'] >= min_price_filter]
    if max_price_filter is not None:
        df_filtered = df_filtered[df_filtered['Prezzo_Numerico'] <= max_price_filter]

st.markdown("---")
st.subheader(f"📋 Elenco Eventi Filtrati ({len(df_filtered)} trovati)")

if not df_filtered.empty:
    df_filtered = df_filtered.sort_values(by=["Fonte", "Luogo"]).reset_index(drop=True)
    col_widths = [0.25, 0.09, 0.09, 0.18, 0.07, 0.07, 0.07, 0.08]
    col_headers = st.columns(col_widths)
    header_style = "background-color: #DDEEE6; padding: 8px 10px; border-bottom: 2px solid var(--primary-color); color: var(--primary-color); font-weight: bold; text-align: left; border-radius: 5px;"

    headers = ["Titolo Evento", "Tipologia", "Fonte", "Luogo", "Prezzo", "Data Inizio", "Data Fine", "Orario"]
    for i, h in enumerate(headers):
        col_headers[i].markdown(f"<div style='{header_style}'>{h}</div>", unsafe_allow_html=True)

    for _, row in df_filtered.iterrows():
        cols = st.columns(col_widths)
        prezzo_formatted = f"€ {row['Prezzo_Numerico']:.2f}" if pd.notna(row['Prezzo_Numerico']) else row.get('Prezzo', "")
        link_html = f"<a href='{row['Link']}' target='_blank'>{row['Titolo']}</a>" if row.get('Link') and row['Link'] != 'Consulta sito' else row['Titolo']
        cols[0].markdown(link_html, unsafe_allow_html=True)
        cols[1].write(row.get('Tipologia', ''))
        cols[2].write(row.get('Fonte', ''))
        cols[3].write(row.get('Luogo', ''))
        cols[4].write(prezzo_formatted)
        cols[5].write(row.get('Data Inizio', ''))
        cols[6].write(row.get('Data Fine', ''))
        cols[7].write(row.get('Orario', ''))

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

    st.markdown("---")
    st.subheader("📊 Analisi Rapida")

    if "Fonte" in df_filtered.columns and not df_filtered["Fonte"].empty:
        source_counts = df_filtered["Fonte"].value_counts()
        if not source_counts.empty:
            st.bar_chart(source_counts)

    if "Tipologia" in df_filtered.columns and not df_filtered["Tipologia"].empty:
        type_counts = df_filtered["Tipologia"].value_counts()
        if not type_counts.empty:
            st.bar_chart(type_counts)
else:
    st.info("Nessun evento corrisponde ai filtri selezionati.")

st.markdown("---")
st.markdown("App creata con ❤️ da Streamlit. Dati aggiornati dallo scraper.")
