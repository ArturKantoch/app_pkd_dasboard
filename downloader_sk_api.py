# downloader_sk_api.py

import os
import pandas as pd
from fetch_quarterly_sk_data import fetch_quarterly_sk_data
from datetime import datetime, timedelta

SAVE_DIR = r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\Kontraktacja"

def _safe_equals(df_old: pd.DataFrame, df_new: pd.DataFrame) -> bool:
    """
    Porównanie z normalizacją kolejności kolumn i typów,
    żeby minimalizować fałszywe różnice.
    """
    if df_old is None or df_new is None:
        return False
    try:
        # Uporządkuj kolumny alfabetycznie i zresetuj indeks
        common_cols = sorted(set(df_old.columns) & set(df_new.columns))
        df_old_norm = df_old[common_cols].reset_index(drop=True)
        df_new_norm = df_new[common_cols].reset_index(drop=True)

        # Dodatkowo postaraj się dopasować typy
        for c in common_cols:
            if df_old_norm[c].dtype != df_new_norm[c].dtype:
                try:
                    df_new_norm[c] = df_new_norm[c].astype(df_old_norm[c].dtype)
                except Exception:
                    pass

        return df_old_norm.equals(df_new_norm)
    except Exception:
        return False

def _process_for_date(target_date_str: str) -> None:
    filename = f"sk_api_quarterly_{target_date_str}.csv"
    filepath = os.path.join(SAVE_DIR, filename)

    try:
        # Pobierz nowe dane (bez zapisu po stronie fetchera)
        df_new = fetch_quarterly_sk_data(target_date_str, save_dir=None, save_csv=False)

        # Brak danych? (np. jeszcze nie ma wstępnych D+1)
        if df_new is None or (isinstance(df_new, pd.DataFrame) and df_new.empty):
            print(f"[SK API] ℹ️ Brak danych dla {target_date_str} (może jeszcze nieopublikowane).")
            return

        # Upewnij się, że to DataFrame
        if not isinstance(df_new, pd.DataFrame):
            print(f"[SK API] ❌ Nieoczekiwany typ danych dla {target_date_str}: {type(df_new)}")
            return

        # Jeśli istnieje poprzednia wersja — porównaj
        if os.path.exists(filepath):
            try:
                df_old = pd.read_csv(filepath)
            except Exception as e_read:
                print(f"[SK API] ⚠️ Nie udało się odczytać istniejącego pliku {filename}: {e_read}")
                df_old = None

            if df_old is not None and _safe_equals(df_old, df_new):
                print(f"[SK API] {target_date_str}: Brak zmian – plik {filename} nie został nadpisany.")
                return
            else:
                print(f"[SK API] {target_date_str}: Wykryto zmianę danych – aktualizuję plik {filename}.")
        else:
            print(f"[SK API] {target_date_str}: Plik {filename} nie istnieje – tworzenie nowego.")

        # Zapisz nową wersję
        os.makedirs(SAVE_DIR, exist_ok=True)
        df_new.to_csv(filepath, index=False)
        print(f"[SK API] {target_date_str}: Zapisano zaktualizowany plik: {filepath}")

    except Exception as e:
        print(f"[SK API] ❌ Błąd podczas pobierania lub porównywania danych dla {target_date_str}: {e}")

def download_latest_sk():
    today = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Najpierw dzień D (dzisiaj)
    _process_for_date(today)

    # Następnie sprawdź, czy są już wstępne dane dla D+1 (jutro)
    _process_for_date(tomorrow)

if __name__ == "__main__":
    download_latest_sk()
