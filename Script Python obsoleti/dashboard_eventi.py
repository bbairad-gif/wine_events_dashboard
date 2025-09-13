import streamlit as st
import pandas as pd

st.set_page_config(page_title="Eventi nel Lazio", layout="wide")
st.title("🍷 Eventi Vino e Cultura nel Lazio")

uploaded_file = "output/eventi_unificati.csv"

try:
    df = pd.read_csv(uploaded_file)

    st.success(f"✅ Caricati {len(df)} eventi")

    fonte = st.selectbox("Filtra per fonte:", ["Tutte", "VisitLazio", "Eventbrite","WineriesExperience"])
    if fonte != "Tutte":
        df = df[df["Fonte"] == fonte]

    # Crea i link cliccabili
    df["Titolo"] = df.apply(lambda row: f"[{row['Titolo']}]({row['Link']})", axis=1)
    df_display = df[["Titolo","Tipologia","Fonte","Data Inizio","Data Fine",  "Orario","Luogo","Prezzo"  ]]  # Nasconde la colonna link

    st.write("### 📋 Elenco Eventi")
    st.write(df_display.to_markdown(index=False), unsafe_allow_html=True)

    st.download_button("📥 Scarica CSV", df.to_csv(index=False), file_name="eventi_lazio.csv")
except FileNotFoundError:
    st.error("⚠️ Nessun file CSV trovato. Esegui prima lo script di scraping.")

