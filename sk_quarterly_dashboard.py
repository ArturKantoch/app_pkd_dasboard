import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 🔁 Odświeżanie dashboardu co 60 sekund
st_autorefresh(interval=60 * 1000, key="data_refresh")

# 🔧 Ustawienia aplikacji
st.set_page_config(page_title="SK Dashboard", layout="wide")
st.title("📊 Stan Zakontraktowania KSE")

# 🔧 Ścieżka do katalogu z plikami CSV
DATA_DIR = r"C:\Users\WQ6674\PycharmProjects\pkd_dasboard\data\Kontraktacja"

# 📅 Wybór daty z domyślnym ustawieniem na dziś
selected_date = st.date_input("📅 Wybierz datę danych", value=date.today(), format="YYYY-MM-DD")

# 🔎 Znajdź najnowszy plik CSV dla wybranej daty
def get_latest_sk_csv_for_date(selected_date):
    date_str = selected_date.strftime("%Y-%m-%d")
    files = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("sk_api_quarterly_") and f.endswith(".csv") and date_str in f
    ]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(DATA_DIR, files[0])

# 📥 Wczytaj dane z cache z automatycznym odświeżaniem co 60 sekund
@st.cache_data(ttl=60)
def load_data(filepath):
    return pd.read_csv(filepath)

# 🎨 Styl różnicy w tabeli
def highlight_diff(val):
    try:
        val = float(val)
        if val > 0:
            return "background-color: rgba(0, 255, 0, 0.2);"  # zielony
        elif val < 0:
            return "background-color: rgba(255, 0, 0, 0.2);"  # czerwony
        else:
            return ""
    except:
        return ""

# 📈 Wizualizacje
def render_dashboard(df: pd.DataFrame, source_file: str):
    df["dtime"] = pd.to_datetime(df["dtime"])
    df["godzina"] = df["dtime"].dt.strftime("%H:%M")
    df["różnica (D - D-1)"] = df["sk_d_fcst"] - df["sk_d1_fcst"]

    st.success(f"✅ Wczytano plik: {os.path.basename(source_file)}")

    # 📋 Tabela
    with st.expander("📋 Pokaż tabelę danych OREB"):
        styled_df = df[["dtime", "sk_d1_fcst", "sk_d_fcst", "różnica (D - D-1)"]].style.map(
            highlight_diff, subset=["różnica (D - D-1)"]
        )
        st.dataframe(styled_df, use_container_width=True)

    # 📈 Liniowy wykres SK D-1 vs D
    st.subheader("📈 Wykres liniowy – SK D-1 vs SK D")
    st.line_chart(df.set_index("dtime")[["sk_d1_fcst", "sk_d_fcst"]])

    # 📊 Wykres kolumnowy z kolorami (plotly)
    st.subheader("📊 Różnice pomiędzy D a D-1")
    colors = ["green" if v > 0 else "red" if v < 0 else "gray" for v in df["różnica (D - D-1)"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["dtime"],
        y=df["różnica (D - D-1)"],
        marker_color=colors
    ))
    fig.update_layout(
        title="Różnice między SK D a D-1",
        xaxis_title="Godzina",
        yaxis_title="MW",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ▶️ Główna logika
def main():
    filepath = get_latest_sk_csv_for_date(selected_date)
    if not filepath:
        st.error(f"❌ Brak dostępnych danych SK dla daty {selected_date.strftime('%Y-%m-%d')}.")
        return

    try:
        df = load_data(filepath)
        render_dashboard(df, filepath)
    except Exception as e:
        st.error(f"❌ Błąd podczas wczytywania danych: {e}")

if __name__ == "__main__":
    main()
