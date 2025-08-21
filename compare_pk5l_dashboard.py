import streamlit as st
import pandas as pd
import os
import plotly.express as px
import time
from streamlit_autorefresh import st_autorefresh

# 🔁 Auto-odświeżanie co 60 sekund
st_autorefresh(interval=60 * 1000, key="pk5l_refresh")

zoom_level = st.sidebar.slider("🔍 Powiększenie interfejsu", 50, 150, 100, step=10)
st.markdown(
    f"""
    <style>
        html {{
            zoom: {zoom_level}% ;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

REFRESH_INTERVAL = 60
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()
if time.time() - st.session_state["last_refresh"] > REFRESH_INTERVAL:
    st.session_state["last_refresh"] = time.time()

# Ustawienia dashboardu
DATA_DIR = r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\plan_5_letni"
st.set_page_config(page_title="Porównanie wersji PK5L", layout="wide")
st.title("📊 Dashboard – Porównanie wersji planu 5-letniego (PK5L)")

# Wczytaj pliki CSV
from datetime import datetime, timedelta

# Wczytaj pliki CSV
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])

# Dostępne daty (wydobycie z nazw plików)
available_dates = sorted(list(set([
    f.split("__")[0].replace("pk5l_", "") for f in files if f.startswith("pk5l_")
])))

# Domyślna data: jutro (jeśli istnieje w danych)
tomorrow_str = (datetime.today() + timedelta(days=1)).strftime("%Y%m%d")
default_index = available_dates.index(tomorrow_str) if tomorrow_str in available_dates else len(available_dates) - 1

# Wybór daty
selected_date = st.sidebar.selectbox("📅 Wybierz datę planu PK5L", available_dates, index=default_index)

# Filtrowanie plików tylko dla wybranej daty
files = sorted([f for f in files if f.startswith(f"pk5l_{selected_date}")])

# files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
if len(files) < 2:
    st.warning("⚠️ W katalogu `plan_5_letni/` muszą znajdować się co najmniej 2 pliki .csv.")
    st.stop()

# Wybór wersji
# Wybór wersji – domyślnie ostatnia vs pierwsza, ale z możliwością zmiany
st.sidebar.header("🔁 Wybierz wersje pliku PK5L do porównania")

# Domyślne: najnowszy i najstarszy plik dla wybranej daty
default_file_new = files[-1]  # najnowszy
default_file_old = files[0]   # najstarszy

file_new = st.sidebar.selectbox("🆕 Nowsza wersja", list(reversed(files)), index=0)  # reversed -> najnowsza domyślnie
# kandydaci do starszej wersji – wszystkie poza wybraną nowszą
file_old_candidates = [f for f in files if f != file_new]
# domyślny index dla starszej wersji: jeśli najnowszy to ostatni plik, wybierz pierwszy
default_old_index = 0 if default_file_new == file_new else file_old_candidates.index(default_file_old) if default_file_old in file_old_candidates else 0

if not file_old_candidates:
    st.warning("⚠️ Wybierz inne pliki do porównania.")
    st.stop()
file_old = st.sidebar.selectbox("📁 Starsza wersja", file_old_candidates, index=default_old_index)

# st.sidebar.header("🔁 Wybierz wersje pliku PK5L do porównania")
# file_new = st.sidebar.selectbox("Nowsza wersja", list(reversed(files)), index=0)
# file_old_candidates = [f for f in reversed(files) if f != file_new]
# if not file_old_candidates:
#     st.warning("⚠️ Wybierz inne pliki do porównania.")
#     st.stop()
# file_old = st.sidebar.selectbox("Starsza wersja", file_old_candidates)

# Wczytanie danych
df_new = pd.read_csv(os.path.join(DATA_DIR, file_new))
df_old = pd.read_csv(os.path.join(DATA_DIR, file_old))

# Dodaj kolumnę suma_oze = wiatr + PV (jeśli obie istnieją)
if "fcst_pv_tot_gen" in df_new.columns and "fcst_wi_tot_gen" in df_new.columns:
    df_new["suma_oze"] = df_new["fcst_pv_tot_gen"] + df_new["fcst_wi_tot_gen"]
if "fcst_pv_tot_gen" in df_old.columns and "fcst_wi_tot_gen" in df_old.columns:
    df_old["suma_oze"] = df_old["fcst_pv_tot_gen"] + df_old["fcst_wi_tot_gen"]
# Mapowanie nazw
column_mapping = {
    "grid_demand_fcst": "Prognozowane zapotrzebowanie sieci [MW]",
    "req_pow_res": "Wymagana rezerwa mocy OSP [MW]",
    "surplus_cap_avail_tso": "Nadwyżka mocy dostępna dla OSP [MW]",
    "gen_surplus_avail_tso_above": "Nadwyżka mocy dostępna dla OSP ponad wymaganą rezerwę mocy [MW]",
    "avail_cap_gen_units_stor_prov": "Moc dyspozycyjna JW i magazynów energii świadczących usługi bilansujące w ramach RB [MW]",
    "avail_cap_gen_units_stor_prov_tso": "Moc dyspozycyjna JW i magazynów energii świadczących usługi bilansujące w ramach RB dostępna dla OSP [MW]",
    "fcst_gen_unit_stor_prov": "Przewidywana generacja JW i magazynów energii świadczących usługi bilansujące w ramach RB [MW]",
    "fcst_gen_unit_stor_non_prov": "Prognozowana generacja JW i magazynów energii nieświadczących usług bilansujących w ramach RB [MW]",
    "fcst_wi_tot_gen": "Prognozowana sumaryczna generacja źródeł wiatrowych [MW]",
    "fcst_pv_tot_gen": "Prognozowana sumaryczna generacja źródeł fotowoltaicznych [MW]",
    "planned_exchange": "Planowane saldo wymiany międzysystemowej [MW]",
    "fcst_unav_energy": "Prognozowana niedyspozycyjność wynikająca z ograniczeń sieciowych [MW]",
    "planned_restr_mwe_avail_shutdown": "Planowane ograniczenia dyspozycyjności i odstawień MWE [MW]",
    "sum_unav_oper_cond": "Suma niedostępności (postoje + ubytki) ze względu na warunki eksploatacyjne (WE) [MW]",
    "pred_gen_res_not_cov": "Przewidywana generacja zasobów wytwórczych nieobjętych obowiązkami mocowymi [MW]",
    "cap_market_obligation": "Obowiązki mocowe wszystkich jednostek rynku mocy [MW]",
    "suma_oze": "Suma generacji OZE (wiatr + PV) [MW]",
}
reverse_mapping = {v: k for k, v in column_mapping.items()}

# Kolumna czasu
common_cols = set(df_new.columns) & set(df_old.columns)
time_col_candidates = [col for col in common_cols if "dtime" in col.lower()]
if not time_col_candidates:
    st.error("⚠️ Brakuje kolumny czasu (np. 'plan_dtime') w plikach.")
    st.stop()
time_col = time_col_candidates[0]
df_new.set_index(time_col, inplace=True)
df_old.set_index(time_col, inplace=True)

# Kolumny liczbowe
numeric_columns = df_new.select_dtypes(include='number').columns
selectable_columns = [col for col in numeric_columns if col in df_old.columns and col in column_mapping]
default_columns = [
    "grid_demand_fcst", "fcst_pv_tot_gen", "fcst_wi_tot_gen",
    "req_pow_res", "cap_market_obligation", "planned_exchange"
]
default_in_data = [col for col in default_columns if col in selectable_columns]

# Multiselect z nazwami Excelowymi
st.sidebar.header("📌 Wybierz kolumny do porównania")
column_display_names = [column_mapping[col] for col in selectable_columns]
default_display_names = [column_mapping[col] for col in default_in_data if col in column_mapping]
selected_display = st.sidebar.multiselect("Kolumny", column_display_names, default=default_display_names)
selected_columns = [reverse_mapping[name] for name in selected_display]

# Porównanie
merged = df_new[selected_columns].subtract(df_old[selected_columns], fill_value=0)
merged["timestamp"] = merged.index

# Tabela różnic
st.subheader("📋 Różnice między wersjami PK5L")
styled_table = merged[selected_columns].rename(columns=column_mapping).style.format("{:+.1f}").map(
    lambda x: "color: green" if x > 0 else "color: red" if x < 0 else "color: gray"
)
with st.expander("📊 Pokaż/ukryj tabelę różnic", expanded=False):
    st.dataframe(styled_table, use_container_width=True)

# Opisy plików
st.markdown(f"**🆕 Nowszy plik:** `{file_new}`")
st.markdown(f"**📁 Starszy plik:** `{file_old}`")

# Histogramy różnic
st.subheader("📊 Interaktywne histogramy różnic")
charts_per_row = st.slider("Liczba wykresów w rzędzie", min_value=2, max_value=4, value=2, step=1)
for i in range(0, len(selected_columns), charts_per_row):
    cols = st.columns(charts_per_row)
    for j in range(charts_per_row):
        if i + j < len(selected_columns):
            col = selected_columns[i + j]
            df_plot = merged.reset_index().copy()
            df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])
            df_plot["color"] = df_plot[col].apply(lambda x: "green" if x > 0 else "red" if x < 0 else "gray")

            fig = px.bar(
                df_plot,
                x="timestamp",
                y=col,
                color="color",
                color_discrete_map={"green": "green", "red": "red", "gray": "gray"},
                title=f"{column_mapping.get(col, col)} – różnice między wersjami",
                labels={"timestamp": "Czas", col: "Zmiana"},
                hover_data={"color": False}
            )
            fig.update_layout(height=350, margin=dict(l=40, r=20, t=40, b=40))
            cols[j].plotly_chart(fig, use_container_width=True)
# === WIZUALIZACJA DANYCH ORYGINALNYCH Z WYBOREM WERSJI ===
st.subheader("📈 Wizualizacja danych oryginalnych (wybrana wersja PK5L)")

original_candidates = sorted([
    f for f in os.listdir(DATA_DIR)
    if f.startswith(f"pk5l_{selected_date}") and f.endswith(".csv")
])

if not original_candidates:
    st.info("Brak dostępnych plików PK5L dla tej daty.")
else:
    # Wybór wersji pliku oryginalnego (domyślnie ostatnia)
    selected_original_file = st.selectbox(
        "📂 Wybierz wersję oryginalnego pliku PK5L do wizualizacji",
        original_candidates,
        index=len(original_candidates) - 1
    )

    # Wczytanie danych
    df_original = pd.read_csv(os.path.join(DATA_DIR, selected_original_file))

    # Dodanie kolumny suma_oze, jeśli potrzebna
    if "fcst_pv_tot_gen" in df_original.columns and "fcst_wi_tot_gen" in df_original.columns:
        df_original["suma_oze"] = df_original["fcst_pv_tot_gen"] + df_original["fcst_wi_tot_gen"]

    numeric_original_cols = df_original.select_dtypes(include="number").columns
    selectable_original_cols = [col for col in numeric_original_cols if col in column_mapping]
    display_original_cols = [column_mapping[col] for col in selectable_original_cols]
    reverse_original_map = {v: k for k, v in column_mapping.items()}

    selected_original_display = st.multiselect(
        "📌 Wybierz kolumny do wizualizacji",
        display_original_cols,
        default=display_original_cols[:2]
    )
    selected_original_cols = [reverse_original_map[c] for c in selected_original_display]

    for i in range(0, len(selected_original_cols), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(selected_original_cols):
                col = selected_original_cols[i + j]
                fig = px.bar(
                    df_original,
                    x=pd.to_datetime(df_original[time_col]),
                    y=col,
                    title=f"{column_mapping.get(col, col)} – {selected_original_file}",
                    labels={"x": "Czas", col: "Wartość"}
                )
                fig.update_layout(height=350, margin=dict(l=40, r=20, t=40, b=40))
                cols[j].plotly_chart(fig, use_container_width=True)

# # === WIZUALIZACJA DANYCH ORYGINALNYCH ===
# st.subheader("📈 Wizualizacja danych oryginalnych (pierwszy plan PK5L dla doby)")
#
# selected_date = file_new.split("__")[0].replace("pk5l_", "")
# original_candidates = sorted([
#     f for f in files if f.startswith(f"pk5l_{selected_date}") and f.endswith(".csv")
# ])
# original_file = original_candidates[0] if original_candidates else None
#
# if not original_file:
#     st.info("Brak dostępnego oryginalnego pliku PK5L dla tej daty.")
# else:
#     df_original = pd.read_csv(os.path.join(DATA_DIR, original_file))
#     # Dodaj suma_oze również w df_original
#     if "fcst_pv_tot_gen" in df_original.columns and "fcst_wi_tot_gen" in df_original.columns:
#         df_original["suma_oze"] = df_original["fcst_pv_tot_gen"] + df_original["fcst_wi_tot_gen"]
#     numeric_original_cols = df_original.select_dtypes(include="number").columns
#     selectable_original_cols = [col for col in numeric_original_cols if col in column_mapping]
#     display_original_cols = [column_mapping[col] for col in selectable_original_cols]
#     reverse_original_map = {v: k for k, v in column_mapping.items()}
#
#
#     selected_original_display = st.multiselect(
#
#         "📌 Wybierz kolumny do wizualizacji",
#         display_original_cols,
#         default=display_original_cols[:2]
#     )
#     selected_original_cols = [reverse_original_map[c] for c in selected_original_display]
#
#     for i in range(0, len(selected_original_cols), 2):
#         cols = st.columns(2)
#         for j in range(2):
#             if i + j < len(selected_original_cols):
#                 col = selected_original_cols[i + j]
#                 fig = px.bar(
#                     df_original,
#                     x=pd.to_datetime(df_original[time_col]),
#                     y=col,
#                     title=f"{column_mapping.get(col, col)} – oryginalny plan PK5L ({selected_date})",
#                     labels={"x": "Czas", col: "Wartość"}
#                 )
#                 fig.update_layout(height=350, margin=dict(l=40, r=20, t=40, b=40))
#                 cols[j].plotly_chart(fig, use_container_width=True)
