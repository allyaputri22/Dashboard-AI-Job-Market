import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as colors

# ---------------------------------------------------------------
# PAGE CONFIG & THEME
# ---------------------------------------------------------------
st.set_page_config(page_title="Dashboard Lowongan Kerja AI", layout="wide")
blue_cyan = ["#00BFFF", "#1E90FF", "#87CEFA", "#4682B4"]
plotly_template = "plotly_dark"

# ---------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------
st.markdown("""
<style>
/* BODY & APP */
.stApp, body { background-color: #1e293b; color: #f7fafc; font-family: 'Segoe UI', sans-serif; }
[data-testid="stSidebar"] { background-color: #2d3748; }

/* SECTION TITLE */
.section-separator { background-color: #2d3748; padding: 15px 35px; border-radius: 10px; margin-top: 25px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); justify-content: center; display: flex; }
.section-separator-title { font-size: 22px; font-weight: 800; color: #f7fafc; margin: 0; }

/* CARD */
div[data-testid="stBlock"] { background-color: #2d3748; padding: 0px 0px; border-radius: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.3); border-left: 6px solid #1E90FF; transition: transform 0.3s ease-in-out; margin-bottom: 15px; }
.chart-card-title { font-size: 15px; font-weight: 800; margin: 0; color: #f7fafc; text-align: center; padding: 15px 20px; border-top-right-radius: 15px; border-top-left-radius: 15px; border-bottom: 1px solid #4a5568; }

/* KPI */
.kpi-box { background-color: #2d3748; padding: 20px 22px; border-radius: 12px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.2); border-left: 4px solid #00BFFF; margin-bottom: 0px; }
.kpi-label { font-size: 13px; color: #a0aec0; margin-bottom: 5px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #00BFFF; }

/* HEADER */
.header-box { background-color: #2d3748; padding: 25px 35px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.4); border-left: 6px solid #1E90FF; justify-content: center; display: flex; }
.header-title { font-size: 24px; font-weight: 800; color: #f7fafc; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------
try:
    df = pd.read_csv("../data/clean_ai_job_market.csv")
except FileNotFoundError:
    st.error("File 'clean_ai_job_market.csv' tidak ditemukan.")
    st.stop()

# Preprocessing
df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
df["year"] = df["posted_date"].dt.year

# Salary avg
if "salary_avg" not in df.columns and "salary_range_usd" in df.columns:
    df["salary_range_usd"] = df["salary_range_usd"].astype(str).str.replace(" ", "", regex=False)
    df[["salary_min","salary_max"]] = df["salary_range_usd"].str.split("-", expand=True)
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
    df["salary_avg"] = (df["salary_min"] + df["salary_max"]) / 2

df_clean = df.dropna(subset=["job_title", "experience_level"]).copy()
df_clean['experience_level'] = df_clean['experience_level'].str.lower().str.strip()

# ---------------------------------------------------------------
# SIDEBAR FILTER
# ---------------------------------------------------------------
st.sidebar.title("Filter Dashboard")
year_list = sorted(df["year"].dropna().unique())
year_list_display = ["All"] + [str(int(y)) for y in year_list]

selected_year = st.sidebar.selectbox("Pilih Tahun", year_list_display)
selected_exp = st.sidebar.multiselect("Pilih Level Pengalaman", options=['entry','mid','senior'], default=['entry','mid','senior'])

# Filter dataframe
df_filtered = df_clean.copy()
if selected_year != "All":
    df_filtered = df_filtered[df_filtered['year'] == int(selected_year)]
df_filtered = df_filtered[df_filtered['experience_level'].isin(selected_exp)]

# ---------------------------------------------------------------
# HEADER & KPI (Total Lowongan + Pekerjaan + Skill + Rata-rata Gaji)
# ---------------------------------------------------------------
st.markdown("<div class='header-box'><span class='header-title'>Dashboard Tren Lowongan Pekerjaan di Bidang AI</span></div>", unsafe_allow_html=True)

# Hitung total lowongan
total_jobs = len(df_filtered)

# Pekerjaan dan skill paling dicari
most_job_title = df_filtered["job_title"].value_counts().idxmax() if len(df_filtered) > 0 else "N/A"
most_skill_series = df_filtered["skills_required"].str.split(", ").explode().dropna().value_counts()
most_skill = most_skill_series.idxmax() if not most_skill_series.empty else "N/A"

# Rata-rata gaji pekerjaan paling banyak dicari
df_salary_filtered = df_filtered.dropna(subset=["salary_avg"])
if most_job_title != "N/A" and most_job_title in df_salary_filtered["job_title"].values:
    avg_salary_filtered = df_salary_filtered[df_salary_filtered["job_title"] == most_job_title]["salary_avg"].mean()
else:
    avg_salary_filtered = df_salary_filtered["salary_avg"].mean() if not df_salary_filtered.empty else 0

# --- LOGIKA DELTA ABSOLUT ---
jobs_prev_year = 0
job_count_delta_html = ""

if selected_year != "All":
    selected_year_int = int(selected_year)
    prev_year_int = selected_year_int - 1
    
    # Hitung jumlah lowongan tahun sebelumnya
    jobs_prev_year = len(df_clean[df_clean['year'] == prev_year_int])
    job_count_selected_year = total_jobs
    
    if jobs_prev_year > 0:
        delta = job_count_selected_year - jobs_prev_year
        if delta > 0:
            color = "green"
            arrow = "↑"
        elif delta < 0:
            color = "red"
            arrow = "↓"
        else:
            color = "gray"
            arrow = ""
        job_count_delta_html = f"""
        <div style='font-size:14px; font-weight:600; color:{color}; margin-top:5px;'>
            {arrow} {abs(delta)} vs Tahun Sebelumnya
        </div>
        """
else:
    job_count_selected_year = total_jobs
    job_count_delta_html = ""  # Tidak ada delta untuk "All"

# ---------------------------------------------------------------
# Tampilkan KPI
# ---------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

# Total Lowongan
with col1:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>{"Total Lowongan" if selected_year=="All" else f"Lowongan Tahun {selected_year}"}</div>
            <div class='kpi-value'>{job_count_selected_year:,}</div>
            {job_count_delta_html}
        </div>
    """, unsafe_allow_html=True)

# Pekerjaan Paling Dicari
with col2:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>Pekerjaan Paling Dicari</div>
            <div class='kpi-value'>{most_job_title}</div>
        </div>
    """, unsafe_allow_html=True)

# Skill Paling Dicari
with col3:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>Skill Paling Dicari</div>
            <div class='kpi-value'>{most_skill}</div>
        </div>
    """, unsafe_allow_html=True)

# Rata-rata Gaji
with col4:
    avg_salary_display = f"${avg_salary_filtered:,.0f}" if avg_salary_filtered > 0 else "N/A"
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>Rata-rata Gaji {most_job_title} (USD)</div>
            <div class='kpi-value'>{avg_salary_display}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")



# ---------------------------------------------------------------
# SECTION 1: Tren + Company Size
# ---------------------------------------------------------------
st.markdown("""<div class='section-separator'><p class='section-separator-title'>Tren Lowongan per Tahun + Persebaran Company Size</p></div>""", unsafe_allow_html=True)
c1, c2 = st.columns(2)

# Tren Lowongan
with c1:
    st.markdown("<div class='chart-card-title'>Tren Lowongan per Tahun</div>", unsafe_allow_html=True)
    trend_year = df_filtered.groupby("year").size().reset_index(name="jumlah_lowongan")
    fig1 = px.line(trend_year, x="year", y="jumlah_lowongan", markers=True, color_discrete_sequence=[blue_cyan[1]], labels={'year':'Tahun','jumlah_lowongan':'Jumlah Lowongan'}, template=plotly_template)
    fig1.update_layout(height=280, margin=dict(l=20,r=20,t=20,b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(type='category'))
    st.plotly_chart(fig1, use_container_width=True)

# Company Size
with c2:
    st.markdown("<div class='chart-card-title'>Persebaran Ukuran Perusahaan</div>", unsafe_allow_html=True)
    company_size_count = df_filtered["company_size"].value_counts().reset_index()
    company_size_count.columns = ["Company Size", "Jumlah Lowongan"]
    fig2 = px.bar(company_size_count, x="Company Size", y="Jumlah Lowongan", color_discrete_sequence=[blue_cyan[2]], template=plotly_template)
    fig2.update_layout(height=280, margin=dict(l=20,r=20,t=20,b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------
# SECTION 2: Skills – Job Title – Industry
# ---------------------------------------------------------------
st.markdown("<div class='section-separator'><p class='section-separator-title'>Skill – Job Title – Industry</p></div>", unsafe_allow_html=True)
c4, c3, c5 = st.columns(3)

# Top Skills
with c4:
    st.markdown("<div class='chart-card-title'>Top 10 Skills Paling Dicari</div>", unsafe_allow_html=True)
    skill_count = df_filtered["skills_required"].str.split(", ").explode().value_counts().head(10).reset_index()
    skill_count.columns = ["Skill", "Jumlah Lowongan"]
    fig4 = px.bar(skill_count, x="Skill", y="Jumlah Lowongan", color_discrete_sequence=[blue_cyan[0]], template=plotly_template)
    fig4.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig4, use_container_width=True)

# Top Job Titles
with c3:
    st.markdown("<div class='chart-card-title'>Top 10 Pekerjaan Paling Dicari</div>", unsafe_allow_html=True)
    job_count = df_filtered["job_title"].value_counts().head(10).reset_index()
    job_count.columns = ["Pekerjaan", "Jumlah Lowongan"]
    fig3 = px.bar(job_count, x="Pekerjaan", y="Jumlah Lowongan", color_discrete_sequence=[blue_cyan[2]], template=plotly_template)
    fig3.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=45)
    st.plotly_chart(fig3, use_container_width=True)

# Industry
with c5:
    st.markdown("<div class='chart-card-title'>Pekerjaan Berdasarkan Industri</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)  # spacing

    df_ind = df_filtered["industry"].value_counts().reset_index()
    df_ind.columns = ["Industry", "Jumlah"]

    # Normalisasi nilai ke 0-1 untuk skala warna
    norm = (df_ind["Jumlah"] - df_ind["Jumlah"].min()) / (df_ind["Jumlah"].max() - df_ind["Jumlah"].min())
    color_scale = [colors.find_intermediate_color('rgb(198, 219, 239)', 'rgb(8, 48, 107)', v, colortype='rgb') for v in norm]

    fig5 = go.Figure(
        go.Pie(
            labels=df_ind["Industry"],
            values=df_ind["Jumlah"],
            marker=dict(colors=color_scale),
            sort=False,
            hovertemplate="<b>%{label}</b><br>Jumlah Lowongan: %{value}<extra></extra>"
        )
    )

    fig5.update_layout(
        height=300, 
        margin=dict(t=30,b=30,l=10,r=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig5, use_container_width=True)
    
st.markdown("---")

# ---------------------------------------------------------------
# SECTION 3: Analisis Gaji & Heatmap Level Pengalaman
# ---------------------------------------------------------------
st.markdown("<div class='section-separator'><p class='section-separator-title'>Analisis Gaji dan Tren Level Pengalaman</p></div>", unsafe_allow_html=True)
c_gaji, c_heatmap = st.columns(2)

# Gaji
with c_gaji:
    st.markdown("<div class='chart-card-title'>Rata-rata Gaji Berdasarkan Pekerjaan dan Level Pengalaman</div>", unsafe_allow_html=True)
    df_salary = df_filtered.dropna(subset=["salary_avg"])
    salary_job_exp = df_salary.groupby(["job_title","experience_level"])["salary_avg"].mean().reset_index()
    salary_colors = {'entry': '#00BFFF', 'mid': '#1E90FF', 'senior': '#4682B4'}
    fig_salary = px.bar(salary_job_exp, x='job_title', y='salary_avg', color='experience_level', color_discrete_map=salary_colors, barmode='group', template=plotly_template, labels={'job_title':'Job Title','salary_avg':'Rata-rata Gaji (USD)','experience_level':'Level'})
    fig_salary.update_layout(height=350, margin=dict(l=60,r=20,t=40,b=20), xaxis_tickangle=45, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_salary, use_container_width=True)

# Heatmap Level
with c_heatmap:
    st.markdown("<div class='chart-card-title'>Tren Permintaan Lowongan Berdasarkan Level Pengalaman</div>", unsafe_allow_html=True)
    
    exp_heatmap = df_filtered.groupby(['experience_level','year']).size().reset_index(name='jumlah_lowongan')
    exp_heatmap = exp_heatmap[exp_heatmap['experience_level'].isin(['entry','mid','senior'])]
    
    pivot_data = exp_heatmap.pivot(index='experience_level', columns='year', values='jumlah_lowongan').fillna(0)
    pivot_data = pivot_data.reindex(['senior','mid','entry'])
    
    fig_heatmap = go.Figure(
        go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns.astype(str),
            y=pivot_data.index.str.title(),
            colorscale='Blues',
            hovertemplate='Tahun: %{x}<br>Level: %{y}<br>Jumlah: %{z}<extra></extra>',
            xgap=2,  # jarak antar kolom
            ygap=2   # jarak antar baris
        )
    )
    
    fig_heatmap.update_layout(
        height=350,
        xaxis_title='Tahun',
        yaxis_title='Level Pengalaman',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20,r=20,t=20,b=20),
        xaxis=dict(tickmode='linear'),
        yaxis=dict(autorange='reversed')  # supaya senior di atas
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
