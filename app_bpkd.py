import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import time
from streamlit_autorefresh import st_autorefresh

# 🔁 Odświeżanie dashboardu co 60 sekund
st_autorefresh(interval=60 * 1000, key="data_refresh")

zoom_level = st.sidebar.slider("🔍 Powiększenie interfejsu", 50, 150, 100, step=10)

# Dynamiczne skalowanie CSS
st.markdown(
    f"""
    <style>
        html {{
            zoom: {zoom_level}%;
        }}
    </style>
    """,
    unsafe_allow_html=True
)
# 🔁 Automatyczne odświeżanie co 60 sekund
REFRESH_INTERVAL = 60  # <- możesz ustawić np. 30 lub 120

# Klucz do zapamiętania czasu ostatniego odświeżenia
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

# Jeśli minęło więcej niż REFRESH_INTERVAL – odśwież stronę
if time.time() - st.session_state["last_refresh"] > REFRESH_INTERVAL:
    st.session_state["last_refresh"] = time.time()

# Ścieżka do katalogu z plikami BPKD
DATA_DIR = r"C:\\Users\\WQ6674\\PycharmProjects\\pkd_dasboard\\data"

st.set_page_config(page_title="Porównanie wersji BPKD", layout="wide")
st.title("📊 Dashboard – Porównanie wersji planu BPKD")

# Wczytanie dostępnych plików
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
if len(files) < 2:
    st.warning("W katalogu `data/` musi znajdować się co najmniej 2 pliki .csv.")
    st.stop()

# Sidebar – wybór wersji BPKD
st.sidebar.header("🔁 Wybierz wersje pliku BPKD do porównania")
file_new = st.sidebar.selectbox("Nowsza wersja", reversed(files), index=0)
file_old = st.sidebar.selectbox("Starsza wersja", reversed(files), index=1)

df_new = pd.read_csv(os.path.join(DATA_DIR, file_new))
df_old = pd.read_csv(os.path.join(DATA_DIR, file_old))

# Sprawdź kolumny wspólne
common_columns = sorted(set(df_new.columns) & set(df_old.columns))
if "dtime" not in common_columns:
    st.error("⚠️ Kolumna 'dtime' musi być obecna w obu plikach.")
    st.stop()

# Znajdź kolumny liczbowe wspólne dla obu plików
numeric_columns = df_new.select_dtypes(include='number').columns
selectable_columns = [col for col in numeric_columns if col in df_old.columns]
# Sidebar – wybór kolumn do porównania
st.sidebar.header("📌 Wybierz kolumny do porównania")

# Domyślne kolumny do analizy
default_columns = [
    "suma_oze",
    "gen_fv",
    "gen_wi",
    "kse_pow_dem",
    "rez_over-demand",
    "rez_under",
    "dom_balance_echange_par",
    "dom_balance_echange_non_par"
]

# Ustaw jako domyślne te z listy default_columns, które faktycznie występują
default_in_data = [col for col in default_columns if col in selectable_columns]

selected_columns = st.sidebar.multiselect("Kolumny", selectable_columns, default=default_in_data)

# Sidebar – wybór kolumn do porównania

# st.sidebar.header("📌 Wybierz kolumny do porównania")
# selected_columns = st.sidebar.multiselect("Kolumny", selectable_columns, default=selectable_columns[:5])

# Dopasowanie danych po czasie
df_old.set_index("dtime", inplace=True)
df_new.set_index("dtime", inplace=True)
merged = df_new[selected_columns].subtract(df_old[selected_columns], fill_value=0)
merged["timestamp"] = merged.index

# Tabela różnic
st.subheader("📋 Różnice między wersjami BPKD")

styled_table = merged[selected_columns].style.format("{:+.1f}").applymap(
    lambda x: "color: green" if x > 0 else "color: red" if x < 0 else "color: gray"
)

with st.expander("📊 Pokaż/ukryj tabelę różnic", expanded=False):  # domyślnie zwinięta
    st.dataframe(styled_table, use_container_width=True)
# st.subheader("📋 Różnice między wersjami BPKD")
# styled_table = merged[selected_columns].style.format("{:+.1f}").applymap(
#     lambda x: "color: green" if x > 0 else "color: red" if x < 0 else "color: gray"
# )
# st.dataframe(styled_table, use_container_width=True)

# # Informacje o czasie publikacji
# st.markdown(f"**🕒 Nowszy plik BPKD:** {file_new.replace('.csv','').replace('BPKD_','').replace('_',' ')}")
# st.markdown(f"**🕒 Starszy plik BPKD:** {file_old.replace('.csv','').replace('BPKD_','').replace('_',' ')}")


st.subheader("📊 Interaktywne histogramy różnic")

# Suwak do ustawiania liczby wykresów w rzędzie
charts_per_row = st.slider("Liczba wykresów w rzędzie", min_value=2, max_value=4, value=2, step=1)

# Informacje o czasie publikacji
st.markdown(f"**🕒 Nowszy plik BPKD:** {file_new.replace('.csv','').replace('BPKD_','').replace('_',' ')}")
st.markdown(f"**🕒 Starszy plik BPKD:** {file_old.replace('.csv','').replace('BPKD_','').replace('_',' ')}")

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
                title=f"{col} – różnice między wersjami",
                labels={"timestamp": "Czas", col: "Zmiana"},
                hover_data={"color": False}
            )

            fig.update_layout(
                xaxis_title="Czas",
                yaxis_title="Zmiana",
                showlegend=False,
                height=350,
                margin=dict(l=40, r=20, t=40, b=40)
            )

            cols[j].plotly_chart(fig, use_container_width=True)

# st.subheader("📊 Interaktywne histogramy różnic")
#
# for i in range(0, len(selected_columns), 2):
#     cols = st.columns(2)
#     for j in range(2):
#         if i + j < len(selected_columns):
#             col = selected_columns[i + j]
#             df_plot = merged.reset_index().copy()
#             df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])
#             df_plot["color"] = df_plot[col].apply(lambda x: "green" if x > 0 else "red" if x < 0 else "gray")
#
#             fig = px.bar(
#                 df_plot,
#                 x="timestamp",
#                 y=col,
#                 color="color",
#                 color_discrete_map={"green": "green", "red": "red", "gray": "gray"},
#                 title=f"{col} – różnice między wersjami",
#                 labels={"timestamp": "Czas", col: "Zmiana"},
#                 hover_data={"color": False}
#             )
#
#             fig.update_layout(
#                 xaxis_title="Czas",
#                 yaxis_title="Zmiana",
#                 showlegend=False,
#                 height=350,
#                 margin=dict(l=40, r=20, t=40, b=40)
#             )
#
#             cols[j].plotly_chart(fig, use_container_width=True)

