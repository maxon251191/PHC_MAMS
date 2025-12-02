import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Қазақстан: АМСК / МӘМС деректерінің аналитикалық панелі")
st.write("Бұл веб-қосымша World Bank деректері негізінде алғашқы медициналық-санитарлық көмектің қолжетімділігі мен сапасын бағалайды.")

# Деректерді оқу
df = pd.read_csv("data/wb_physicians_kz.csv")
df_clean = df.dropna()
df_clean["year"] = df_clean["year"].astype(int)
df_clean = df_clean.sort_values("year")

st.subheader("Дәрігерлер саны (1000 тұрғынға) — динамика")
st.dataframe(df_clean)

# График жасау
fig, ax = plt.subplots(figsize=(10,5))
ax.plot(df_clean["year"], df_clean["physicians_per_1000"], marker="o")
ax.set_xlabel("Жыл")
ax.set_ylabel("1000 адамға шаққандағы дәрігерлер саны")
ax.set_title("Қазақстандағы дәрігерлер тығыздығының динамикасы (2000–2023)")
ax.grid(True)

st.pyplot(fig)

st.success("Streamlit қосымшасы сәтті жүктелді!")
# Жыл диапазоны фильтрі
min_year = int(df_clean["year"].min())
max_year = int(df_clean["year"].max())

year_range = st.slider(
    "Жыл диапазонын таңдаңыз",
    min_year, max_year, (min_year, max_year)
)

df_filtered = df_clean[(df_clean["year"] >= year_range[0]) &
                       (df_clean["year"] <= year_range[1])]
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df_filtered["year"], df_filtered["physicians_per_1000"], marker="o")
...
import plotly.express as px

fig_plotly = px.line(
    df_filtered,
    x="year",
    y="physicians_per_1000",
    markers=True,
    title="Қазақстандағы дәрігерлер тығыздығы (интерактивті график)"
)

st.plotly_chart(fig_plotly, use_container_width=True)
col1, col2, col3 = st.columns(3)

col1.metric("Ең жоғары көрсеткіш", f"{df_clean['physicians_per_1000'].max():.2f}")
col2.metric("Ең төменгі көрсеткіш", f"{df_clean['physicians_per_1000'].min():.2f}")
col3.metric("Орташа мән", f"{df_clean['physicians_per_1000'].mean():.2f}")
csv_data = df_clean.to_csv(index=False).encode("utf-8")
st.download_button(
    label="CSV файлды жүктеу",
    data=csv_data,
    file_name="physicians_kz_clean.csv",
    mime="text/csv"
)

