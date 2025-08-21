import requests
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join("data", "PKD")
os.makedirs(DATA_DIR, exist_ok=True)


def get_date_str(days_offset=0):
    return (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")


def is_pkd_file_already_downloaded(date_str):
    expected_filename = f"PKD_{date_str}.csv"
    return expected_filename in os.listdir(DATA_DIR)


def download_pkd_for_date(date_str):
    url = (
        f"https://v2.api.raporty.pse.pl/api/pdgopkd?"
        f"$filter=business_date eq '{date_str}'&"
        f"$orderby=business_date asc&$first=20000"
    )

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Błąd pobierania danych PKD ({date_str}): {response.status_code}")
            return False

        json_data = response.json()
        if "value" not in json_data or not json_data["value"]:
            print(f"⚠️ Brak danych w odpowiedzi PKD dla {date_str}.")
            return False

        df = pd.DataFrame(json_data["value"])

        if "gen_fv" in df.columns and "gen_wi" in df.columns:
            df["sume_oze"] = df["gen_fv"] + df["gen_wi"]
        else:
            print("⚠️ Brak kolumn 'gen_fv' lub 'gen_wi' — nie dodano 'sume_oze'.")

        filename = f"PKD_{date_str}.csv"
        filepath = os.path.join(DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"✅ Zapisano plik PKD: {filename}")
        return True

    except Exception as e:
        print(f"❌ Błąd pobierania PKD dla {date_str}: {e}")
        return False


def get_missing_pkd_dates():
    existing_files = os.listdir(DATA_DIR)
    existing_dates = set()

    for file in existing_files:
        if file.startswith("PKD_") and file.endswith(".csv"):
            try:
                date_str = file[4:-4]
                datetime.strptime(date_str, "%Y-%m-%d")  # walidacja formatu
                existing_dates.add(date_str)
            except ValueError:
                continue

    # Zakres od najstarszej do dziś
    if existing_dates:
        earliest = min(datetime.strptime(d, "%Y-%m-%d") for d in existing_dates)
    else:
        earliest = datetime.now() - timedelta(days=30)  # domyślnie ostatnie 30 dni

    today = datetime.now().date()
    all_dates = [
        (earliest + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((today - earliest.date()).days + 1)
    ]

    return [d for d in all_dates if d not in existing_dates]


def run_pkd_downloader():
    now = datetime.now()
    if not (15 <= now.hour <= 22):
        return  # poza dozwolonym oknem czasowym

    # Uzupełnij zaległe pliki PKD
    missing_dates = get_missing_pkd_dates()
    if missing_dates:
        print(f"🔄 Uzupełnianie brakujących plików PKD: {missing_dates}")
        for date_str in missing_dates:
            download_pkd_for_date(date_str)

    # Dodatkowo sprawdź dziś i jutro
    for offset in [0, 1]:
        date_str = get_date_str(offset)
        if not is_pkd_file_already_downloaded(date_str):
            download_pkd_for_date(date_str)


if __name__ == "__main__":
    run_pkd_downloader()
