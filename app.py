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
