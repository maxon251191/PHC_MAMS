# app.py
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Ожидание КДУ — Analytics")

st.title("Ожидание КДУ (Almaty) — Interactive analytics")
st.markdown(
    "Upload the Excel file (or use repo `data/` file). The app reads sheets `2020`, `2021`, `2022`, `all` if available."
)

@st.cache_data
def read_excel_sheets(file_bytes):
    """
    Returns dict: sheet_name -> DataFrame
    Accepts bytes of an Excel file or path string.
    """
    if isinstance(file_bytes, (str,)):
        # path on disk
        xls = pd.ExcelFile(file_bytes)
    else:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets = {}
    for sheet in xls.sheet_names:
        try:
            df = xls.parse(sheet)
            sheets[sheet] = df
        except Exception as e:
            st.warning(f"Could not parse sheet {sheet}: {e}")
    return sheets

def unify_sheets(sheets_dict):
    # If there is an 'all' sheet, prefer it; else concat 2020-2022 where present.
    if "all" in sheets_dict:
        df_all = sheets_dict["all"].copy()
    else:
        parts = []
        for s in ["2020","2021","2022"]:
            if s in sheets_dict:
                parts.append(sheets_dict[s])
        if parts:
            df_all = pd.concat(parts, ignore_index=True, sort=False)
        else:
            # fallback: concatenate whatever sheets exist
            df_all = pd.concat(list(sheets_dict.values()), ignore_index=True, sort=False)
    return df_all

def smart_parse_dates(df):
    # try detect 'year' column and convert to int if possible
    if "year" in df.columns:
        try:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        except Exception:
            pass
    return df

# Sidebar: upload or use repo file
st.sidebar.header("Data source")
use_upload = st.sidebar.radio("Choose data source", ["Upload Excel file", "Use repository file (data/...)"])

sheets = {}
file_uploaded = None
repo_path = "data/Ождание КДУ города Алматы.xlsx"  # fallback path
repo_alt = "data/wb_physicians_kz.csv"  # keep as example

if use_upload == "Upload Excel file":
    uploaded = st.sidebar.file_uploader("Upload Excel file (xlsx)", type=["xlsx","xls"])
    if uploaded is not None:
        file_uploaded = uploaded.getvalue()
        try:
            sheets = read_excel_sheets(file_uploaded)
            st.sidebar.success(f"Loaded sheets: {', '.join(list(sheets.keys()))}")
        except Exception as e:
            st.sidebar.error(f"Error reading uploaded file: {e}")
else:
    # attempt to read from disk path in repo
    try:
        sheets = read_excel_sheets(repo_path)
        st.sidebar.success(f"Loaded repo file: {repo_path} (sheets: {', '.join(list(sheets.keys()))})")
    except Exception:
        # try alternative common csv in data/
        try:
            df_alt = pd.read_csv(repo_alt)
            sheets = {"csv_default": df_alt}
            st.sidebar.success(f"Loaded CSV {repo_alt}")
        except Exception as e:
            st.sidebar.warning("No repo file found. Please upload Excel file.")
            sheets = {}

if not sheets:
    st.info("Please upload your Excel file (left panel) or add it to repository `data/` folder.")
    st.stop()

# Combine/choose sheet
default_sheetnames = list(sheets.keys())
selected_sheet = st.sidebar.selectbox("Select sheet to view / analyze", options=default_sheetnames + ["unify_all"])
if selected_sheet == "unify_all":
    df = unify_sheets(sheets)
else:
    df = sheets[selected_sheet].copy()

df = smart_parse_dates(df)

st.subheader("Raw data preview")
st.dataframe(df.head(200), use_container_width=True)

# Basic info / cleaning helpers
st.sidebar.header("Data cleaning / options")
dropna = st.sidebar.checkbox("Drop rows with all-NaN", value=True)
if dropna:
    df = df.dropna(how="all")
# try to infer numeric columns
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# if none, try to convert columns that look numeric
if not num_cols:
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','.'),
                                    errors='coerce')
        except Exception:
            pass
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
if "year" in df.columns and "year" not in cat_cols:
    # ensure year is recognized as categorical for filters but numeric for plots
    if "year" not in num_cols:
        try:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            if "year" not in num_cols:
                num_cols.append("year")
        except Exception:
            pass

st.sidebar.markdown(f"Detected numeric cols: `{', '.join(num_cols)}`")
st.sidebar.markdown(f"Detected categorical cols: `{', '.join(cat_cols)}`")

# Filters: if year column present, show slider or multiselect
st.sidebar.header("Filters")
filters = {}
if "year" in df.columns:
    years = sorted([int(y) for y in df["year"].dropna().unique().astype(int)])
    if years:
        yr_min, yr_max = min(years), max(years)
        yr_range = st.sidebar.slider("Year range", min_value=yr_min, max_value=yr_max, value=(yr_min, yr_max))
        filters["year"] = yr_range

# generic categorical filters (show up to 3 cols)
for col in cat_cols[:3]:
    vals = df[col].dropna().unique().tolist()
    if len(vals) <= 30:
        pick = st.sidebar.multiselect(f"Filter {col}", options=sorted(vals), default=sorted(vals))
        filters[col] = pick

# Apply filters
df_filtered = df.copy()
if "year" in filters:
    y0, y1 = filters["year"]
    df_filtered = df_filtered[(df_filtered["year"] >= y0) & (df_filtered["year"] <= y1)]
for col in cat_cols[:3]:
    if col in filters and filters[col]:
        df_filtered = df_filtered[df_filtered[col].isin(filters[col])]

st.subheader("Filtered data (first 200 rows)")
st.dataframe(df_filtered.head(200), use_container_width=True)

# Statistics panel
st.subheader("Statistics and summary")
col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.markdown("**Rows**")
    st.metric("Total rows (filtered)", len(df_filtered))
with col2:
    st.markdown("**Numeric columns**")
    st.write(num_cols)
with col3:
    st.markdown("**Nulls**")
    st.write(df_filtered.isna().sum().sort_values(ascending=False).head(10))

if num_cols:
    st.markdown("**Descriptive statistics**")
    st.dataframe(df_filtered[num_cols].describe().T)

# Plotting controls
st.subheader("Interactive plots")
plot_type = st.selectbox("Choose plot", ["Line (time series)", "Bar", "Box", "Scatter", "Histogram", "Heatmap (correlation)"])

if plot_type == "Line (time series)":
    if "year" not in df_filtered.columns:
        st.warning("No 'year' column found for time series.")
    else:
        y_col = st.selectbox("Numeric column to plot", options=[c for c in num_cols if c!="year"])
        if y_col:
            agg = st.selectbox("Aggregation", ["mean","median","sum","none"])
            if agg == "none":
                fig = px.line(df_filtered, x="year", y=y_col, markers=True, title=f"{y_col} over year")
            else:
                grouped = df_filtered.groupby("year")[y_col].agg(agg).reset_index()
                fig = px.line(grouped, x="year", y=y_col, markers=True, title=f"{agg} of {y_col} by year")
            st.plotly_chart(fig, use_container_width=True)

elif plot_type == "Bar":
    x = st.selectbox("X (categorical)", options=cat_cols + (["year"] if "year" in df_filtered.columns else []))
    y = st.selectbox("Y (numeric)", options=num_cols)
    if x and y:
        aggfunc = st.selectbox("Aggregate function", ["mean","sum","median","count"])
        if aggfunc == "count":
            aggdf = df_filtered.groupby(x).size().reset_index(name="count")
            fig = px.bar(aggdf, x=x, y="count", title=f"Count by {x}")
        else:
            aggdf = df_filtered.groupby(x)[y].agg(aggfunc).reset_index()
            fig = px.bar(aggdf, x=x, y=y, title=f"{aggfunc} of {y} by {x}")
        st.plotly_chart(fig, use_container_width=True)

elif plot_type == "Box":
    y = st.selectbox("Numeric", options=num_cols)
    x = st.selectbox("Group by (optional)", options=[None] + cat_cols)
    if x:
        fig = px.box(df_filtered, x=x, y=y, points="outliers")
    else:
        fig = px.box(df_filtered, y=y, points="outliers")
    st.plotly_chart(fig, use_container_width=True)

elif plot_type == "Scatter":
    x = st.selectbox("X numeric", options=num_cols)
    y = st.selectbox("Y numeric", options=num_cols, index=1 if len(num_cols)>1 else 0)
    color = st.selectbox("Color by (optional)", options=[None] + cat_cols)
    if x and y:
        fig = px.scatter(df_filtered, x=x, y=y, color=color, trendline="ols")
        st.plotly_chart(fig, use_container_width=True)

elif plot_type == "Histogram":
    colh = st.selectbox("Column", options=num_cols)
    bins = st.slider("Bins", 5, 100, 20)
    fig = px.histogram(df_filtered, x=colh, nbins=bins)
    st.plotly_chart(fig, use_container_width=True)

elif plot_type == "Heatmap (correlation)":
    numeric = df_filtered.select_dtypes(include=[np.number]).dropna(axis=1, how='all')
    if numeric.shape[1] < 2:
        st.warning("Not enough numeric columns for correlation heatmap.")
    else:
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation heatmap")
        st.plotly_chart(fig, use_container_width=True)

# Pivot table / download
st.subheader("Pivot and download")
pivot_cols = st.multiselect("Index (rows) for pivot", options=cat_cols, default=cat_cols[:1])
value_col = st.selectbox("Value (numeric) for aggregation", options=num_cols)
aggfun = st.selectbox("Aggregation", ["mean","sum","median","count"], index=0)
if pivot_cols and value_col:
    pivot = pd.pivot_table(df_filtered, index=pivot_cols, values=value_col, aggfunc=aggfun).reset_index()
    st.dataframe(pivot)
    csv = pivot.to_csv(index=False).encode("utf-8")
    st.download_button(label="Download pivot as CSV", data=csv, file_name="pivot.csv", mime="text/csv")

# provide raw CSV download of filtered data
st.sidebar.header("Export")
if st.sidebar.button("Download filtered data CSV"):
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("Click to download", data=csv, file_name="filtered_data.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.info("If you want me to prepare a GitHub-ready repo and deploy, tell me and I'll produce the files (app.py, requirements.txt, README) and the sample article text in English.")
