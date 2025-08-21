import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
from datetime import datetime, timedelta


def download_latest_pk5l():
    output_dir = r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\plan_5_letni"
    os.makedirs(output_dir, exist_ok=True)

    # Daty dostawy: dziś, jutro, pojutrze
    today = datetime.today().date()
    delivery_dates = [today + timedelta(days=i) for i in range(3)]

    url = "https://v2.api.raporty.pse.pl/api/pk5l-wp"

    for business_date in delivery_dates:
        start = f"{business_date}T00:00:00"
        end = f"{business_date + timedelta(days=1)}T00:00:00"

        params = {
            "$filter": f"plan_dtime gt '{start}' and plan_dtime le '{end}'",
            "$orderby": "plan_dtime asc",
            "$first": "20000"
        }

        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            data = response.json()["value"]
            df_new = pd.DataFrame(data)

            if df_new.empty:
                print(f"[PK5L] ⏩ Brak danych dla daty dostawy {business_date}.")
                continue

            # Szukaj najnowszego istniejącego pliku dla tej daty
            existing_files = sorted([
                f for f in os.listdir(output_dir)
                if f.startswith(f"pk5l_{business_date}") and f.endswith(".csv")
            ])

            if existing_files:
                latest_file = existing_files[-1]
                df_last = pd.read_csv(os.path.join(output_dir, latest_file))

                if df_new.equals(df_last):
                    print(f"[PK5L] Brak zmian dla {business_date} – nowa wersja nie została zapisana.")
                    continue
                else:
                    print(f"[PK5L] Wykryto zmiany dla {business_date} – zapisuję nową wersję.")
            else:
                print(f"[PK5L] Brak wcześniejszego pliku dla {business_date} – zapisuję pierwszą wersję.")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pk5l_{business_date}__{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)
            df_new.to_csv(filepath, index=False, encoding='utf-8-sig')

            print(f"[PK5L] ✅ Zapisano nową wersję planu 5-letniego: {filename}")

        except Exception as e:
            print(f"[PK5L] ❌ Błąd podczas pobierania danych dla {business_date}: {e}")
