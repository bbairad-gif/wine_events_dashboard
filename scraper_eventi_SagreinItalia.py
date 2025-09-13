import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_sagreinitalia():
    url = "https://www.sagreinitalia.it"
    eventi = []

    # La pagina principale elenca le sagre in sezioni
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Trova tutte le sezioni evento (esempio)
    sezioni = soup.find_all("div", class_="event-preview")  # adattare se serve

    for s in sezioni:
        titolo = s.find("h3")
        luogo = s.find("span", class_="location")
        data = s.find("span", class_="date")

        if titolo:
            eventi.append({
                "Titolo": titolo.text.strip(),
                "Data": data.text.strip() if data else "",
                "Luogo": luogo.text.strip() if luogo else "",
                "Link": url,
                "Fonte": "Sagreinitalia.it"
            })

    # Salva file CSV
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(eventi)
    df.to_csv("output/eventi_sagreinitalia.csv", index=False, encoding="utf-8-sig")
    print(f"✅ Salvati {len(eventi)} eventi da Sagreinitalia")

# Per test
if __name__ == "__main__":
    scrape_sagreinitalia()
