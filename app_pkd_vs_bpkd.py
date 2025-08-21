import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 🔁 Odświeżanie dashboardu co 60 sekund
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Ścieżki do folderów
DATA_DIR = r"C:\\Users\\WQ6674\\PycharmProjects\\pkd_dasboard\\data"
BPKD_DIR = DATA_DIR
PKD_DIR = os.path.join(DATA_DIR, "PKD")

# Kolumny ignorowane w porównaniu
IGNORED_COLUMNS = ["dtime_utc", "period_utc", "publication_ts_utc"]

# Domyślne kolumny do porównań
DEFAULT_COLUMNS = [
    "suma_oze",
    "gen_fv",
    "gen_wi",
    "kse_pow_dem",
    "rez_over_demand",
    "rez_under",
    "dom_balance_echange_par",
    "dom_balance_echange_non_par"
]


def load_latest_bpkd_file_for_date(date_str):
    bpkd_files = [f for f in os.listdir(BPKD_DIR) if f.startswith(f"BPKD_{date_str}_") and f.endswith(".csv")]
    if not bpkd_files:
        return None, None
    latest_file = sorted(bpkd_files)[-1]
    df = pd.read_csv(os.path.join(BPKD_DIR, latest_file))
    return df, latest_file


def load_previous_bpkd_file_for_date(date_str):
    bpkd_files = [f for f in os.listdir(BPKD_DIR) if f.startswith(f"BPKD_{date_str}_") and f.endswith(".csv")]
    if len(bpkd_files) < 2:
        return None
    previous_file = sorted(bpkd_files)[-2]
    df = pd.read_csv(os.path.join(BPKD_DIR, previous_file))
    return df


def load_pkd_file(date_str):
    pkd_file = f"PKD_{date_str}.csv"
    path = os.path.join(PKD_DIR, pkd_file)
    if not os.path.exists(path):
        return None, None
    df = pd.read_csv(path)
    return df, pkd_file


def get_bpkd_versions_for_date(date_str):
    return sorted([
        f for f in os.listdir(BPKD_DIR)
        if f.startswith(f"BPKD_{date_str}_") and f.endswith(".csv")
    ])

def highlight_changes(diff_from_pkd, diff_from_prev):
    if pd.notna(diff_from_prev) and diff_from_prev != 0:
        return "background-color: yellow"
    elif pd.notna(diff_from_pkd) and diff_from_pkd != 0:
        return "background-color: orange"
    return ""


def main():
    st.set_page_config(layout="wide")
    st.title("Porównanie PKD z najnowszym BPKD")

    available_pkd_files = sorted([f for f in os.listdir(PKD_DIR) if f.startswith("PKD_")])
    available_dates = [f.replace("PKD_", "").replace(".csv", "") for f in available_pkd_files]

    selected_date = st.selectbox("Wybierz datę planu PKD", available_dates[::-1])

    pkd_df, pkd_file = load_pkd_file(selected_date)
    # bpkd_df, bpkd_file = load_latest_bpkd_file_for_date(selected_date)
    # Lista wersji BPKD
    bpkd_versions = get_bpkd_versions_for_date(selected_date)
    if not bpkd_versions:
        st.error("Brak dostępnych wersji BPKD dla wybranej daty.")
        return

    # Domyślnie ostatnia (najnowsza)
    default_bpkd_version = bpkd_versions[-1]
    selected_bpkd_file = st.selectbox("Wybierz wersję planu BPKD", bpkd_versions[::-1], index=0)
    bpkd_df = pd.read_csv(os.path.join(BPKD_DIR, selected_bpkd_file))

    bpkd_file = selected_bpkd_file  # 🔧 [DODANE] przypisanie nazwy pliku BPKD, aby działał odczyt czasu

    prev_bpkd_df = load_previous_bpkd_file_for_date(selected_date)

    if pkd_df is None or bpkd_df is None:
        st.error("Brak danych do porównania.")
        return


    for col in IGNORED_COLUMNS:
        bpkd_df = bpkd_df.drop(columns=[col], errors="ignore")
        if prev_bpkd_df is not None:
            prev_bpkd_df = prev_bpkd_df.drop(columns=[col], errors="ignore")

    pkd_df = pkd_df.sort_values(by=["dtime"]).reset_index(drop=True)
    # ✅ Dodaj suma_oze do PKD, jeśli brakuje
    if "suma_oze" not in pkd_df.columns and "gen_wi" in pkd_df.columns and "gen_fv" in pkd_df.columns:
        pkd_df["suma_oze"] = pkd_df["gen_wi"] + pkd_df["gen_fv"]
    bpkd_df = bpkd_df.sort_values(by=["dtime"]).reset_index(drop=True)
    if prev_bpkd_df is not None:
        prev_bpkd_df = prev_bpkd_df.sort_values(by=["dtime"]).reset_index(drop=True)

    numeric_cols = pkd_df.select_dtypes(include='number').columns.tolist()
    default_cols = [col for col in DEFAULT_COLUMNS if col in numeric_cols]
    selected_cols = st.multiselect("Wybierz kolumny do analizy", numeric_cols, default=default_cols)


    diff_df = bpkd_df.copy()
    for col in selected_cols:
        if col in bpkd_df.columns:
            diff_df[f"{col}_diff_pkd"] = bpkd_df[col] - pkd_df[col]
            if prev_bpkd_df is not None:
                diff_df[f"{col}_diff_prev"] = bpkd_df[col] - prev_bpkd_df[col]
            else:
                diff_df[f"{col}_diff_prev"] = 0


    def apply_highlighting(row):
        styles = []
        for col in diff_columns:  # <- tylko te kolumny, które faktycznie istnieją
            base_col = col.replace("_diff_pkd", "")
            diff_pkd = row.get(f"{base_col}_diff_pkd")
            diff_prev = row.get(f"{base_col}_diff_prev")
            style = highlight_changes(diff_pkd, diff_prev)
            styles.append(style)
        return styles

    bpkd_time = "brak informacji"
    try:
        bpkd_time = datetime.strptime(bpkd_file.split("_")[-1].replace(".csv", ""), "%H-%M-%S").strftime("%H:%M:%S")
    except Exception:
        pass

    pkd_time = "brak informacji"
    try:
        pkd_mtime = os.path.getmtime(os.path.join(PKD_DIR, pkd_file))
        pkd_time = datetime.fromtimestamp(pkd_mtime).strftime("%H:%M:%S")
    except Exception:
        pass

    # st.markdown(f"**🕒 PKD:** {selected_date} {pkd_time}  ")
    # st.markdown(f"**🕒 BPKD:** {selected_date} {bpkd_time}")

    st.subheader("Tabela różnic")
    # diff_columns = [f"{col}_diff_pkd" for col in selected_cols]
    diff_columns = [f"{col}_diff_pkd" for col in selected_cols if f"{col}_diff_pkd" in diff_df.columns]

    styled_df = diff_df[diff_columns].style.apply(apply_highlighting, axis=1)

    with st.expander("📊 Pokaż/ukryj tabelę różnic między BPKD a PKD", expanded=False):

        st.dataframe(styled_df, use_container_width=True)

    num_cols = st.slider("Ile wykresów obok siebie?", min_value=2, max_value=4, value=2, step=1)

    st.subheader("Wizualizacja różnic względem PKD")
    st.markdown(f"**🕒 PKD:** {selected_date} {pkd_time}  ")
    st.markdown(f"**🕒 BPKD:** {selected_date} {bpkd_time}")

    for i in range(0, len(selected_cols), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(selected_cols):
                col = selected_cols[i + j]
                col_name = f"{col}_diff_pkd"
                if col_name in diff_df.columns:
                    fig = go.Figure()
                    colors = ["green" if v > 0 else ("red" if v < 0 else "gray") for v in diff_df[col_name]]
                    fig.add_trace(go.Bar(
                        x=pd.to_datetime(diff_df["dtime"]),
                        y=diff_df[col_name],
                        marker_color=colors
                    ))
                    fig.update_layout(
                        title=f"{col} – różnice między wersjami",
                        xaxis_title="Czas",
                        yaxis_title="Zmiana",
                        height=400
                    )
                    cols[j].plotly_chart(fig, use_container_width=True)


    st.subheader("Wizualizacja danych oryginalnych")
    plan_type = st.radio("Wybierz plan do wykresu:", ["PKD", "BPKD"], horizontal=True)
    selected_original_cols = st.multiselect("Wybierz kolumny do wizualizacji", numeric_cols, default=numeric_cols[:2])
    df = pkd_df if plan_type == "PKD" else bpkd_df

    for i in range(0, len(selected_original_cols), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(selected_original_cols):
                col = selected_original_cols[i + j]
                fig = px.bar(df, x=pd.to_datetime(df["dtime"]), y=col,
                             title=f"{col} – {plan_type}",
                             labels={"x": "Czas", col: "Wartość"})
                cols[j].plotly_chart(fig, use_container_width=True)



if __name__ == "__main__":
    main()
