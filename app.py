import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 頁面設定 ---
st.set_page_config(page_title="異常事件戰情室 V7", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# --- 初始化 session state ---
if 'selected_event' not in st.session_state:
    st.session_state.selected_event = None
if 'selected_dept' not in st.session_state:
    st.session_state.selected_dept = None
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# --- 六版風格 CSS 樣式 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
    
    * {
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    /* 整體背景 - 六版風格 */
    .main { 
        background-color: #f3f7fa !important;
        padding: 1rem 2rem;
    }
    
    /* 玻璃卡片效果 */
    .glass-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
        border-radius: 2rem;
        padding: 2rem;
    }
    
    /* 標題區域 */
    h1 {
        color: #0f172a !important;
        font-weight: 900 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    
    /* KPI 卡片樣式 - 六版風格 */
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 3rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.75rem !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.98) !important;
        padding: 2rem !important;
        border-radius: 2rem !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-bottom: 4px solid #4f46e5 !important;
        transition: transform 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
    }
    
    /* 篩選器容器 - 六版風格 */
    .filter-container {
        background: rgba(255, 255, 255, 0.98) !important;
        padding: 1.5rem 2rem;
        border-radius: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 2rem;
        backdrop-filter: blur(8px);
    }
    
    /* 標籤樣式 */
    label {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 0.875rem !important;
    }
    
    /* 選單樣式 */
    .stSelectbox label, .stMultiselect label {
        color: #0f172a !important;
    }
    
    /* 頁籤樣式 - 六版風格 */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 4px;
        background: #e2e8f0 !important;
        padding: 4px;
        border-radius: 1rem;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        font-weight: 700 !important;
        font-size: 0.875rem !important;
        border-radius: 0.75rem;
        background: transparent;
        color: #64748b !important;
        transition: all 0.3s;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        color: #1e293b !important;
        background: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* 內容區域 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* 圖表容器 - 六版風格 */
    [data-testid="stPlotlyChart"] {
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 2.5rem !important;
        padding: 2rem !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
    }
    
    /* 資料表格 - 六版風格，支援完整滾動 */
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 2.5rem !important;
        padding: 0 !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        overflow: visible !important;
    }
    
    /* 表格容器完整滾動支援 */
    .dataframe-container {
        overflow-x: auto !important;
        overflow-y: auto !important;
        width: 100% !important;
        max-height: 600px !important;
        border-radius: 2.5rem;
    }
    
    .dataframe-container table {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    /* 按鈕樣式 - 六版風格 */
    .stButton > button {
        background: #4f46e5 !important;
        color: white !important;
        border: none !important;
        border-radius: 1rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button:hover {
        background: #4338ca !important;
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stDownloadButton > button {
        background: #4f46e5 !important;
        color: white !important;
    }
    
    /* 上傳檔案區域 - 六版風格 */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.98) !important;
        padding: 2rem !important;
        border-radius: 2rem !important;
        border: 2px dashed #4f46e5 !important;
    }
    
    /* 資訊卡片 - 六版風格 */
    .info-card {
        background: rgba(255, 255, 255, 0.98) !important;
        padding: 2rem !important;
        border-radius: 2rem !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        margin: 1rem 0;
    }
    
    /* 提示訊息 */
    .stAlert {
        border-radius: 1rem !important;
    }
    
    /* 深色模式適配 */
    @media (prefers-color-scheme: dark) {
        .main {
            background-color: #0f172a !important;
        }
        
        .glass-card, .filter-container, .stMetric {
            background: rgba(30, 41, 59, 0.98) !important;
            border-color: rgba(51, 65, 85, 0.8) !important;
        }
        
        [data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
        }
        
        label {
            color: #f1f5f9 !important;
        }
        
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
            background: rgba(30, 41, 59, 0.98) !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background: #1e293b !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: #334155 !important;
            color: #60a5fa !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 核心邏輯：事件類別清洗 ---
def clean_event_category(text):
    text = str(text).strip()
    # 使用正則表達式只抓取「某某事件」這四個字
    match = re.search(r'[\u4e00-\u9fa5]{2}事件', text)
    return match.group(0) if match else "其他事件"

def load_data(file):
    try:
        xl = pd.ExcelFile(file)
        all_data = []
        
        for sheet in xl.sheet_names:
            try:
                df_temp = pd.read_excel(file, sheet_name=sheet, header=None, nrows=25)
                header_row = -1
                for i, row in df_temp.iterrows():
                    if "單號" in [str(x) for x in row.values]:
                        header_row = i
                        break
                
                if header_row != -1:
                    df = pd.read_excel(file, sheet_name=sheet, header=header_row)
                    df = df.loc[:, ~df.columns.duplicated()] # 刪除重複標題
                    
                    # 智慧對應：114年叫新事件類別，其他叫事件類別
                    target_col = "新事件類別" if "新事件類別" in df.columns else "事件類別"
                    
                    if target_col in df.columns:
                        # 重點：清理事件類別，只留「XX事件」
                        df["事件類別"] = df[target_col].apply(clean_event_category)
                    
                    # 統一必要欄位
                    rename_map = {"發生部門": "發生單位", "通報日期": "日期"}
                    df.rename(columns=rename_map, inplace=True)
                    
                    # 篩選出需要的欄位並合併
                    keep = ["單號", "日期", "事件類別", "發生單位", "事件描述"]
                    valid_cols = [c for c in keep if c in df.columns]
                    if valid_cols:  # 確保有有效欄位
                        temp_df = df[valid_cols].copy()
                        temp_df["年度"] = sheet
                        all_data.append(temp_df)
            except Exception as e:
                st.warning(f"讀取工作表 '{sheet}' 時發生錯誤，已跳過：{str(e)}")
                continue

        return pd.concat(all_data, ignore_index=True) if all_data else None
    except Exception as e:
        st.error(f"讀取 Excel 檔案時發生錯誤：{str(e)}")
        return None

# --- UI 介面 - 六版風格 ---
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown("""
        <div style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <span style="padding: 0.75rem; background: #4f46e5; border-radius: 1rem; color: white; font-size: 1.5rem;">🛡️</span>
                <h1 style="margin: 0; color: #0f172a; font-weight: 900; font-size: 2.5rem; letter-spacing: -0.02em;">醫療異常事件分析儀表板</h1>
            </div>
            <p style="color: #64748b; font-weight: 500; margin-left: 4rem; font-size: 1rem;">自動分析類別件數與事由 · 支援多年度數據合併</p>
        </div>
    """, unsafe_allow_html=True)

with col_header2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 重置", use_container_width=True, key="header_reset_btn"):
        st.session_state.selected_event = None
        st.session_state.selected_dept = None
        st.session_state.selected_year = None
        st.rerun()

uploaded_file = st.file_uploader("📁 上傳 Excel / CSV 檔案", type=["xlsx"], help="支援 .xlsx 格式，系統將自動分析多個工作表")

if uploaded_file:
    with st.spinner("正在讀取和分析 Excel 檔案..."):
        df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        # --- 頂部篩選區 (簡潔下拉樣式 - 六版風格) ---
        st.markdown("""
            <div class="filter-container" style="padding: 1.5rem 2rem;">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.25rem;">📅</span>
                    <h3 style="margin: 0; font-size: 0.875rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b;">資料篩選</h3>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 簡潔的三欄布局
        c1, c2, c3 = st.columns(3)
        with c1:
            years = st.multiselect(
                "年度", 
                sorted(df["年度"].unique()), 
                default=sorted(df["年度"].unique()),
                key="filter_years"
            )
        with c2:
            types = st.multiselect(
                "事件類別", 
                sorted(df["事件類別"].unique()), 
                default=sorted(df["事件類別"].unique()),
                key="filter_types"
            )
        with c3:
            depts = st.multiselect(
                "發生單位", 
                sorted(df["發生單位"].unique()), 
                default=sorted(df["發生單位"].unique()),
                key="filter_depts"
            )
        
        # 重置按鈕單獨一行，右對齊
        col_reset1, col_reset2 = st.columns([5, 1])
        with col_reset2:
            if st.button("🔄 重置", use_container_width=True, key="filter_reset_btn"):
                st.session_state.selected_event = None
                st.session_state.selected_dept = None
                st.session_state.selected_year = None
                st.rerun()
        
        f_df = df[(df["年度"].isin(years)) & (df["事件類別"].isin(types)) & (df["發生單位"].isin(depts))]

        # --- KPI 卡片 (專業儀表板風格) ---
        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        
        total_cases = len(f_df)
        k1.metric("📊 總案件數", f"{total_cases:,}", delta=None)
        
        if not f_df.empty and "事件類別" in f_df.columns and not f_df["事件類別"].mode().empty:
            main_risk = f_df["事件類別"].mode()[0]
            risk_count = len(f_df[f_df["事件類別"] == main_risk])
            k2.metric("⚠️ 主要風險", main_risk, delta=f"{risk_count} 件")
        else:
            k2.metric("⚠️ 主要風險", "-", delta=None)

        # --- 主要內容區 ---
        tab_total, tab_trend, tab_data, tab_detail = st.tabs(["📌 統計總覽", "📈 趨勢分析", "📋 資料明細", "🔍 點擊詳情"])
        
        with tab_total:
            # 第一行：兩個主要圖表
            col_l, col_r = st.columns([1, 1])
            
            with col_l:
                st.markdown("### 🎯 事件分布比率")
                if not f_df.empty and "事件類別" in f_df.columns:
                    event_counts = f_df["事件類別"].value_counts()
                    # 六版風格配色
                    category_colors = {
                        '心跳事件': '#F43F5E', '管路事件': '#3B82F6', '跌倒事件': '#F59E0B',
                        '公共事件': '#10B981', '藥物事件': '#8B5CF6', '其他事件': '#64748B',
                        '輸血事件': '#BE123C', '檢查檢驗': '#06B6D4', '傷害事件': '#EF4444'
                    }
                    colors_list = [category_colors.get(cat, '#94a3b8') for cat in event_counts.index]
                    
                    fig_pie = px.pie(
                        values=event_counts.values, 
                        names=event_counts.index, 
                        hole=0.72,
                        color_discrete_sequence=colors_list
                    )
                    fig_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>數量: %{value}<br>占比: %{percent}<extra></extra>'
                    )
                    fig_pie.update_layout(
                        showlegend=True, 
                        margin=dict(t=40, b=40, l=40, r=40, pad=10),
                        height=400,
                        font=dict(size=12),
                        autosize=True
                    )
                    
                    # 使用 on_select 處理點擊事件
                    selected_pie = st.plotly_chart(
                        fig_pie, 
                        use_container_width=True, 
                        key="pie_chart",
                        on_select="rerun"
                    )
                    
                    # 處理選擇事件
                    if selected_pie and hasattr(selected_pie, 'selection') and selected_pie.selection.points:
                        point = selected_pie.selection.points[0]
                        if hasattr(point, 'label') and point.label:
                            st.session_state.selected_event = point.label
                            st.success(f"✅ 已選擇：{point.label}，請切換到「🔍 點擊詳情」頁籤查看")
                            st.rerun()
                    
                else:
                    st.info("無資料可顯示")
            
            with col_r:
                st.markdown("### 🏢 單位發生次數排名")
                if "發生單位" in f_df.columns and not f_df["發生單位"].empty:
                    dept_rank = f_df["發生單位"].value_counts().reset_index()
                    dept_rank.columns = ["發生單位", "count"]
                    dept_rank = dept_rank.head(15)
                    fig_bar = px.bar(
                        dept_rank, 
                        x="count", 
                        y="發生單位", 
                        orientation='h',
                        text="count", 
                        color="count", 
                        color_continuous_scale='Blues',
                        color_discrete_sequence=['#4f46e5']
                    )
                    fig_bar.update_traces(
                        hovertemplate='<b>%{y}</b><br>案件數: %{x}<extra></extra>'
                    )
                    fig_bar.update_layout(
                        showlegend=False, 
                        yaxis={'categoryorder':'total ascending'},
                        margin=dict(t=40, b=40, l=80, r=40, pad=10),
                        height=400,
                        xaxis_title="案件數量",
                        yaxis_title="",
                        autosize=True
                    )
                    selected_bar = st.plotly_chart(
                        fig_bar, 
                        use_container_width=True, 
                        key="bar_chart",
                        on_select="rerun"
                    )
                    
                    # 處理選擇事件
                    if selected_bar and hasattr(selected_bar, 'selection') and selected_bar.selection.points:
                        point = selected_bar.selection.points[0]
                        if hasattr(point, 'y') and point.y:
                            st.session_state.selected_dept = point.y
                            st.success(f"✅ 已選擇：{point.y}，請切換到「🔍 點擊詳情」頁籤查看")
                            st.rerun()
                    
                else:
                    st.info("無資料可顯示")
            
            # 第二行：年度分布和事件類別趨勢
            st.markdown("<br>", unsafe_allow_html=True)
            col_l2, col_r2 = st.columns([1, 1])
            
            with col_l2:
                st.markdown("### 📅 年度案件分布")
                if not f_df.empty and "年度" in f_df.columns:
                    year_counts = f_df["年度"].value_counts().sort_index()
                    fig_year = px.bar(
                        x=year_counts.index,
                        y=year_counts.values,
                        labels={'x': '年度', 'y': '案件數'},
                        color=year_counts.values,
                        color_continuous_scale='Viridis'
                    )
                    fig_year.update_traces(
                        text=year_counts.values,
                        textposition='outside',
                        hovertemplate='<b>%{x} 年</b><br>案件數: %{y}<extra></extra>'
                    )
                    fig_year.update_layout(
                        showlegend=False,
                        margin=dict(t=40, b=60, l=60, r=40, pad=10),
                        height=350,
                        xaxis_title="年度",
                        yaxis_title="案件數量",
                        autosize=True
                    )
                    selected_year_chart = st.plotly_chart(
                        fig_year, 
                        use_container_width=True, 
                        key="year_chart",
                        on_select="rerun"
                    )
                    
                    # 處理選擇事件
                    if selected_year_chart and hasattr(selected_year_chart, 'selection') and selected_year_chart.selection.points:
                        point = selected_year_chart.selection.points[0]
                        if hasattr(point, 'x') and point.x:
                            st.session_state.selected_year = str(point.x)
                            st.success(f"✅ 已選擇：{point.x} 年，請切換到「🔍 點擊詳情」頁籤查看")
                            st.rerun()
                else:
                    st.info("無資料可顯示")
            
            with col_r2:
                st.markdown("### 📊 事件類別統計")
                if not f_df.empty and "事件類別" in f_df.columns:
                    event_stats = f_df["事件類別"].value_counts().head(10)
                    fig_event = px.bar(
                        x=event_stats.index,
                        y=event_stats.values,
                        labels={'x': '事件類別', 'y': '案件數'},
                        color=event_stats.values,
                        color_continuous_scale='Reds'
                    )
                    fig_event.update_traces(
                        text=event_stats.values,
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>案件數: %{y}<extra></extra>'
                    )
                    fig_event.update_layout(
                        showlegend=False,
                        margin=dict(t=40, b=100, l=60, r=40, pad=10),
                        height=350,
                        xaxis_title="事件類別",
                        yaxis_title="案件數量",
                        xaxis_tickangle=-45,
                        autosize=True
                    )
                    st.plotly_chart(fig_event, use_container_width=True, key="event_chart")
                else:
                    st.info("無資料可顯示")

        with tab_trend:
            st.markdown("### 📈 跨年度案件趨勢分析")
            
            if not f_df.empty and "年度" in f_df.columns and "事件類別" in f_df.columns:
                trend = f_df.groupby(["年度", "事件類別"]).size().reset_index(name="件數")
                if not trend.empty:
                    # 折線圖
                    fig_trend = px.line(
                        trend, 
                        x="年度", 
                        y="件數", 
                        color="事件類別", 
                        markers=True,
                        line_shape='spline',
                        title="各事件類別跨年度趨勢"
                    )
                    fig_trend.update_traces(
                        line=dict(width=3),
                        marker=dict(size=8),
                        hovertemplate='<b>%{fullData.name}</b><br>年度: %{x}<br>件數: %{y}<extra></extra>'
                    )
                    fig_trend.update_layout(
                        height=500,
                        margin=dict(t=50, b=60, l=60, r=50, pad=10),
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        autosize=True
                    )
                    selected_trend = st.plotly_chart(
                        fig_trend, 
                        use_container_width=True, 
                        key="trend_chart",
                        on_select="rerun"
                    )
                    
                    # 處理選擇事件
                    if selected_trend and hasattr(selected_trend, 'selection') and selected_trend.selection.points:
                        point = selected_trend.selection.points[0]
                        if hasattr(point, 'fullData') and hasattr(point.fullData, 'name'):
                            st.session_state.selected_event = point.fullData.name
                        if hasattr(point, 'x'):
                            st.session_state.selected_year = str(point.x)
                        st.success("✅ 已選擇圖表資料，請切換到「🔍 點擊詳情」頁籤查看")
                        st.rerun()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 熱力圖
                    col_l3, col_r3 = st.columns([2, 1])
                    with col_l3:
                        st.markdown("#### 🔥 年度-事件類別熱力圖")
                        pivot_trend = trend.pivot(index="事件類別", columns="年度", values="件數").fillna(0)
                        fig_heatmap = px.imshow(
                            pivot_trend,
                            labels=dict(x="年度", y="事件類別", color="件數"),
                            color_continuous_scale='YlOrRd',
                            aspect="auto"
                        )
                        fig_heatmap.update_layout(height=400)
                        st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap")
                    
                    with col_r3:
                        st.markdown("#### 📊 趨勢統計")
                        st.markdown(f"""
                        <div class="info-card">
                            <p><strong>總事件類別數：</strong>{trend['事件類別'].nunique()}</p>
                            <p><strong>涵蓋年度數：</strong>{trend['年度'].nunique()}</p>
                            <p><strong>最高單年件數：</strong>{trend['件數'].max()}</p>
                            <p><strong>平均年度件數：</strong>{round(trend['件數'].mean(), 1)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("無資料可顯示")
            else:
                st.info("無資料可顯示")

        with tab_data:
            st.markdown("### 📋 完整事件清單")
            
            # 顯示資料統計
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("顯示筆數", f"{len(f_df):,}")
            with col_info2:
                st.metric("總欄位數", f"{len(f_df.columns)}")
            with col_info3:
                if not f_df.empty:
                    csv = f_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 下載 CSV", csv, "filtered_data.csv", "text/csv", use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 資料表格
            if not f_df.empty:
                # 重新排列欄位順序
                display_cols = ["年度", "單號", "日期", "事件類別", "發生單位", "事件描述"]
                available_cols = [col for col in display_cols if col in f_df.columns]
                other_cols = [col for col in f_df.columns if col not in display_cols]
                final_cols = available_cols + other_cols
                
                # 使用更好的表格容器支援完整滾動
                st.markdown("""
                    <div class="dataframe-container">
                """, unsafe_allow_html=True)
                st.dataframe(
                    f_df[final_cols], 
                    use_container_width=True, 
                    height=500,
                    hide_index=True,
                    column_config={
                        col: st.column_config.TextColumn(
                            col, 
                            width="large" if col == "事件描述" else "medium"
                        ) 
                        for col in final_cols
                    }
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("目前篩選條件下無資料可顯示")
        
        with tab_detail:
            st.markdown("### 🔍 圖表點擊詳情")
            st.markdown("**提示：** 點擊上方圖表中的資料點，或使用下方快速選擇按鈕來查看詳細資料")
            
            # 快速選擇按鈕區域
            st.markdown("---")
            st.markdown("#### 🎯 快速選擇")
            
            col_quick1, col_quick2 = st.columns(2)
            
            with col_quick1:
                st.markdown("**事件類別快速選擇：**")
                if not f_df.empty and "事件類別" in f_df.columns:
                    event_counts = f_df["事件類別"].value_counts()
                    quick_cols = st.columns(min(3, len(event_counts)))
                    for idx, (event_name, count) in enumerate(event_counts.head(6).items()):
                        with quick_cols[idx % len(quick_cols)]:
                            if st.button(f"{event_name}\n({count})", key=f"quick_event_{event_name}", use_container_width=True):
                                st.session_state.selected_event = event_name
                                st.session_state.selected_dept = None
                                st.session_state.selected_year = None
                                st.rerun()
            
            with col_quick2:
                st.markdown("**單位快速選擇：**")
                if not f_df.empty and "發生單位" in f_df.columns:
                    dept_rank = f_df["發生單位"].value_counts().head(6)
                    quick_cols = st.columns(min(3, len(dept_rank)))
                    for idx, (dept_name, count) in enumerate(dept_rank.items()):
                        with quick_cols[idx % len(quick_cols)]:
                            if st.button(f"{dept_name}\n({count})", key=f"quick_dept_{dept_name}", use_container_width=True):
                                st.session_state.selected_dept = dept_name
                                st.session_state.selected_event = None
                                st.session_state.selected_year = None
                                st.rerun()
            
            st.markdown("---")
            
            detail_df = None
            
            # 根據點擊的項目顯示對應資料
            if st.session_state.selected_event:
                st.success(f"✅ 已選擇事件類別：**{st.session_state.selected_event}**")
                detail_df = f_df[f_df["事件類別"] == st.session_state.selected_event].copy()
            
            if st.session_state.selected_dept:
                st.info(f"🏢 已選擇單位：**{st.session_state.selected_dept}**")
                if detail_df is not None:
                    detail_df = detail_df[detail_df["發生單位"] == st.session_state.selected_dept]
                else:
                    detail_df = f_df[f_df["發生單位"] == st.session_state.selected_dept].copy()
            
            if st.session_state.selected_year:
                st.info(f"📅 已選擇年度：**{st.session_state.selected_year}**")
                if detail_df is not None:
                    detail_df = detail_df[detail_df["年度"] == st.session_state.selected_year]
                else:
                    detail_df = f_df[f_df["年度"] == st.session_state.selected_year].copy()
            
            if detail_df is not None and not detail_df.empty:
                st.markdown(f"#### 📊 符合條件的資料（共 {len(detail_df)} 筆）")
                
                # 顯示統計
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.metric("案件數", len(detail_df))
                with stat_col2:
                    if "發生單位" in detail_df.columns:
                        st.metric("涉及單位", detail_df["發生單位"].nunique())
                with stat_col3:
                    if "事件類別" in detail_df.columns:
                        st.metric("事件類型", detail_df["事件類別"].nunique())
                
                # 顯示資料
                display_cols = ["年度", "單號", "日期", "事件類別", "發生單位", "事件描述"]
                available_cols = [col for col in display_cols if col in detail_df.columns]
                
                # 使用更好的表格容器支援完整滾動
                st.markdown("""
                    <div class="dataframe-container">
                """, unsafe_allow_html=True)
                st.dataframe(
                    detail_df[available_cols],
                    use_container_width=True,
                    height=400,
                    hide_index=True,
                    column_config={
                        col: st.column_config.TextColumn(
                            col, 
                            width="large" if col == "事件描述" else "medium"
                        ) 
                        for col in available_cols
                    }
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 下載按鈕
                csv_detail = detail_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 下載此篩選結果 (CSV)", 
                    csv_detail, 
                    f"detail_{st.session_state.selected_event or 'data'}.csv", 
                    "text/csv"
                )
            else:
                st.info("👆 請使用上方的快速選擇按鈕，或點擊圖表中的資料點來查看詳細資訊")
    
    elif df is not None and df.empty:
        st.warning("Excel 檔案已讀取，但未找到符合格式的資料。請確認檔案包含「單號」欄位。")
    else:
        st.error("無法讀取 Excel 檔案，請確認檔案格式是否正確。")

else:
    # 未上傳時的導引畫面
    st.info("請上傳 Excel 檔案以啟用儀表板。系統將自動合併多個工作表數據並清理格式。")
    st.markdown("""
    ### 📋 使用說明
    1. **上傳 Excel 檔案**：支援 .xlsx 格式
    2. **自動識別**：系統會自動尋找包含「單號」的標題列
    3. **多工作表處理**：自動合併所有工作表資料
    4. **資料清理**：自動統一欄位名稱並清理事件類別格式
    5. **即時分析**：上傳後立即顯示統計圖表和資料明細
    """)
