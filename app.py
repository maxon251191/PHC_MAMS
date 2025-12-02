import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ожидание КДУ (Almaty)", layout="wide")

st.title("Ожидание КДУ (Almaty) — Interactive Analytics")
st.write("Upload the Excel file or use repository data/. The app reads sheets **2020**, **2021**, **2022**, **all**.")

# ---------------------------
# SIDEBAR
# ---------------------------

st.sidebar.header("Data source")

source = st.sidebar.radio("Choose data source:", 
                          ["Upload Excel file", "Use repository file (data/…)"])


def load_excel(path):
    """Load 4 sheets: 2020, 2021, 2022, all"""
    xls = pd.ExcelFile(path)
    df_dict = {}

    for sheet in ["2020", "2021", "2022", "all"]:
        if sheet in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            df.columns = df.columns.astype(str)
            df_dict[sheet] = df

    return df_dict


# ---------------------------
# LOAD FILE
# ---------------------------

uploaded_file = None
dfs = {}

if source == "Upload Excel file":
    uploaded_file = st.sidebar.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

    if uploaded_file:
        dfs = load_excel(uploaded_file)
        st.sidebar.success(f"Loaded sheets: {', '.join(dfs.keys())}")

else:
    # Repository: data/ folder
    try:
        dfs = load_excel("data/Ожидание КДУ города Алматы.xlsx")
        st.sidebar.success("Loaded data from repository")
    except:
        st.sidebar.error("Repository file not found!")

# Stop if no data
if not dfs:
    st.stop()


# ---------------------------
# SELECT SHEET
# ---------------------------

sheet = st.sidebar.selectbox("Select sheet to analyze", list(dfs.keys()))
df = dfs[sheet].copy()

st.subheader(f"Dataset: **{sheet}**")
st.dataframe(df, use_container_width=True)


# ---------------------------
# FILTERS
# ---------------------------

st.subheader("Filters")

# Column selection
cols = st.multiselect("Select columns to filter", df.columns)

for col in cols:
    vals = sorted(df[col].dropna().unique().tolist())
    if len(vals) <= 50:
        pick = st.multiselect(f"Filter {col}", vals, default=vals)
        df = df[df[col].isin(pick)]
    else:
        min_val = df[col].min()
        max_val = df[col].max()
        rng = st.slider(f"{col} range", min_value=float(min_val), max_value=float(max_val),
                        value=(float(min_val), float(max_val)))
        df = df[(df[col] >= rng[0]) & (df[col] <= rng[1])]

st.write("Filtered data:")
st.dataframe(df, use_container_width=True)


# ---------------------------
# CHARTS
# ---------------------------

st.subheader("Charts")

# Numerical columns only
num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(exclude="number").columns.tolist()

if len(num_cols) >= 1:
    ycol = st.selectbox("Choose numeric column for chart", num_cols)

    fig1 = px.line(df, x=df.index, y=ycol, title=f"Dynamic of {ycol}")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.histogram(df, x=ycol, title=f"Distribution of {ycol}")
    st.plotly_chart(fig2, use_container_width=True)

if len(cat_cols) >= 1:
    colcat = st.selectbox("Choose categorical column", cat_cols)

    fig3 = px.pie(df, names=colcat, title=f"Distribution: {colcat}")
    st.plotly_chart(fig3, use_container_width=True)

