import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# Ustawienia katalogu zapisu
OUTPUT_DIR = "pk5l_versions"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data biznesowa – jutro
business_date = (datetime.today() + timedelta(days=1)).date()
start = f"{business_date}T00:00:00"
end = f"{business_date + timedelta(days=1)}T00:00:00"

# Pobieranie danych z API
url = "https://v2.api.raporty.pse.pl/api/pk5l-wp"
params = {
    "$filter": f"plan_dtime gt '{start}' and plan_dtime le '{end}'",
    "$orderby": "plan_dtime asc",
    "$first": "20000"
}

response = requests.get(url, params=params)
data = response.json()["value"]
df = pd.DataFrame(data)

# Tworzenie nazwy pliku
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"pk5l_{business_date}__{timestamp}.csv"
filepath = os.path.join(OUTPUT_DIR, filename)

# Zapis danych
df.to_csv(filepath, index=False, encoding='utf-8-sig')
print(f"Zapisano plik: {filepath}")

