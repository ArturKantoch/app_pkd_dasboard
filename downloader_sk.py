import os
from datetime import datetime
import pandas as pd
from sk_d1_d_prog_downloader import fetch_sk_data_and_save

def download_latest_sk():
    today = datetime.today().strftime("%Y-%m-%d")
    save_dir = r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\Kontraktacja"
    filename = f"sk_{today}.csv"
    filepath = os.path.join(save_dir, filename)

    # Pobierz najnowsze dane z API jako DataFrame
    try:
        from sk_d1_d_prog_downloader import fetch_sk_data
        df_new = fetch_sk_data(today)
    except Exception as e:
        print(f"[SK] Błąd podczas pobierania danych: {e}")
        return

    if os.path.exists(filepath):
        try:
            df_old = pd.read_csv(filepath)
            # Porównanie – tylko jeśli różnią się wartości
            if not df_new.equals(df_old):
                df_new.to_csv(filepath, index=False)
                print(f"[SK] Wykryto nową wersję – zapisano zaktualizowane dane do {filename}")
            else:
                print(f"[SK] Brak zmian – plik {filename} nie został nadpisany.")
        except Exception as e:
            print(f"[SK] Błąd przy porównaniu lub odczycie pliku: {e}")
    else:
        os.makedirs(save_dir, exist_ok=True)
        df_new.to_csv(filepath, index=False)
        print(f"[SK] Plik {filename} nie istniał – zapisano nowe dane.")
