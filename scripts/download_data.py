import os
import pandas as pd
import requests

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

def download(url, filename):
    print(f"Downloading: {url}")
    r = requests.get(url)
    r.raise_for_status()
    path = f"{DATA_DIR}/{filename}"
    with open(path, "wb") as f:
        f.write(r.content)
    print("Saved:", path)

# World Bank: Physicians per 1,000 population
def wb_physicians():
    url = "http://api.worldbank.org/v2/country/KZ/indicator/SH.MED.PHYS.ZS?format=json&per_page=2000"
    r = requests.get(url)
    data = r.json()[1]

    df = pd.DataFrame(data)[["date","value"]]
    df.columns = ["year","physicians_per_1000"]
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year")

    df.to_csv(f"{DATA_DIR}/wb_physicians_kz.csv", index=False)
    print("✔ WB physicians data saved")

if __name__ == "__main__":
    wb_physicians()
