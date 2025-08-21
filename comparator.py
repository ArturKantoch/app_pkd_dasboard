import os
import pandas as pd
from datetime import datetime

# Konfiguracja
DATA_DIR = "data"
COMPARE_COLUMNS = ["kse_pow_dem", "gen_wi", "gen_fv", "rez_over_demand", "rez_under"]
OUTPUT_DIFF = "diff_{}.csv".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

def find_latest_files(folder, count=2):
    files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    files = sorted(files)
    return [os.path.join(folder, f) for f in files[-count:]]

def compare_versions(file_old, file_new, columns):
    df_old = pd.read_csv(file_old)
    df_new = pd.read_csv(file_new)

    result = pd.DataFrame()
    for col in columns:
        if col in df_old.columns and col in df_new.columns:
            result[f"{col}_diff"] = df_new[col] - df_old[col]

    if "dtime" in df_new.columns:
        result["timestamp"] = df_new["dtime"]
    elif "period" in df_new.columns:
        result["timestamp"] = df_new["period"]
    else:
        result["timestamp"] = range(len(df_new))

    return result

def main():
    if not os.path.exists(DATA_DIR):
        print("❌ Folder 'data/' nie istnieje.")
        return

    latest_files = find_latest_files(DATA_DIR)
    if len(latest_files) < 2:
        print("⚠️ Brakuje dwóch wersji plików do porównania.")
        return

    file_old, file_new = latest_files
    print(f"🔍 Porównuję:\n- starszy: {file_old}\n- nowszy:  {file_new}")

    diff_df = compare_versions(file_old, file_new, COMPARE_COLUMNS)
    diff_df.to_csv(OUTPUT_DIFF, index=False)
    print(f"✅ Zapisano różnice do pliku: {OUTPUT_DIFF}")

if __name__ == "__main__":
    main()
