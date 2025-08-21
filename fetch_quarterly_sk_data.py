import requests
import pandas as pd
import os

def fetch_quarterly_sk_data(business_date: str, save_dir: str = None, save_csv: bool = True):
    """
    Pobiera dane kwartalne SK z API PSE dla podanej daty (business_date)
    i zapisuje do CSV (jeśli save_csv = True)

    Args:
        business_date (str): Format 'YYYY-MM-DD'
        save_dir (str): Ścieżka folderu do zapisu CSV
        save_csv (bool): Czy zapisać plik CSV

    Returns:
        pd.DataFrame: Dane z API
    """
    url = (
        f"https://api.raporty.pse.pl/api/sk?"
        f"$filter=business_date eq '{business_date}'&"
        f"$orderby=period asc&$first=2000"
    )

    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json().get("value", [])
    if not data:
        raise ValueError(f"Brak danych SK dla daty {business_date}")

    df = pd.DataFrame(data)

    # Dodajmy kolumnę tylko z datą i nazwijmy kwadrans
    df["data"] = pd.to_datetime(df["dtime"]).dt.date
    df["kwadrans"] = df["period"]

    # Uporządkuj kolumny
    ordered_cols = ["data", "kwadrans", "sk_d1_fcst", "sk_d_fcst", "sk_cost",
                    "dtime", "dtime_utc", "period", "period_utc", "business_date",
                    "publication_ts", "publication_ts_utc"]

    df = df[[col for col in ordered_cols if col in df.columns]]

    # Zapisz jako CSV
    if save_csv and save_dir:
        os.makedirs(save_dir, exist_ok=True)
        filename = f"sk_api_quarterly_{business_date}.csv"
        filepath = os.path.join(save_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"✅ Dane zapisane do: {filepath}")

    return df

# Przykład uruchomienia
if __name__ == "__main__":
    fetch_quarterly_sk_data(
        business_date="2025-07-25",
        save_dir=r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\Kontraktacja"
    )
