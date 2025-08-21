import requests
import pandas as pd
import hashlib
import os
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = "data"

def download_bpdk_for_date(target_date: datetime):
    headers = {"Accept": "application/json"}
    date_str = target_date.strftime('%Y-%m-%d')
    base_url = "https://v2.api.raporty.pse.pl/api/pdgobpkd"

    params = {
        "$filter": f"business_date eq '{date_str}'",
        "$orderby": "business_date asc",
        "$first": "20000"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, verify=False)
        if response.status_code != 200:
            print(f"❌ Błąd pobierania danych dla {date_str}: {response.status_code}")
            return None

        json_data = response.json()
        if "value" not in json_data or not json_data["value"]:
            print(f"⚠️ Odpowiedź API dla {date_str} jest pusta.")
            return None

        df = pd.DataFrame(json_data["value"])

        # ✅ Dodanie kolumny suma_oze
        if 'gen_fv' in df.columns and 'gen_wi' in df.columns:
            df['suma_oze'] = df['gen_fv'] + df['gen_wi']

        content_bytes = df.to_csv(index=False).encode("utf-8")
        checksum = hashlib.md5(content_bytes).hexdigest()

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        for filename in sorted(os.listdir(DATA_DIR), reverse=True):
            if filename.endswith(".csv") and date_str in filename:
                with open(os.path.join(DATA_DIR, filename), "rb") as f:
                    if hashlib.md5(f.read()).hexdigest() == checksum:
                        print(f"✅ Brak zmian w planie BPKD dla {date_str}.")
                        return None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"BPKD_{date_str}_{timestamp}.csv"
        filepath = os.path.join(DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"💾 Zapisano nową wersję planu BPKD dla {date_str}: {filename}")
        return df, filepath

    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych dla {date_str}: {e}")
        return None

def download_latest_bpdk():
    today = datetime.today()
    tomorrow = today + timedelta(days=1)

    print("⏬ Pobieranie planu BPKD dla dzisiaj (D)")
    download_bpdk_for_date(today)

    print("⏬ Pobieranie planu BPKD dla jutra (D+1)")
    download_bpdk_for_date(tomorrow)
