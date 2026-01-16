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

# --- 專業儀表板 CSS 樣式 ---
st.markdown("""
    <style>
    /* 整體背景 */
    .main { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
    }
    
    /* 標題區域 */
    h1 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 0.5rem !important;
    }
    
    /* KPI 卡片樣式 */
    [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.3);
    }
    
    /* 篩選器容器 */
    .filter-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* 標籤樣式 */
    label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    
    /* 選單樣式 */
    .stSelectbox label, .stMultiselect label {
        color: #4b5563 !important;
    }
    
    /* 頁籤樣式 */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px;
        background: rgba(255, 255, 255, 0.95);
        padding: 0.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        font-weight: 600;
        font-size: 15px;
        border-radius: 6px;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* 內容區域 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 圖表容器 */
    [data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 資料表格 */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 按鈕樣式 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 上傳檔案區域 */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px dashed #667eea;
    }
    
    /* 資訊卡片 */
    .info-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
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

# --- UI 介面 ---
st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: white; margin: 0;">📊 異常事件分析儀表板</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; margin-top: 0.5rem;">數據驅動決策 · 異常事件即時監測系統</p>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📁 上傳 Excel 檔案", type=["xlsx"], help="支援 .xlsx 格式，系統將自動分析多個工作表")

if uploaded_file:
    with st.spinner("正在讀取和分析 Excel 檔案..."):
        df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        # --- 頂部篩選區 (專業卡片樣式) ---
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown("### 🔍 資料篩選")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            years = st.multiselect("📅 年度", sorted(df["年度"].unique()), default=sorted(df["年度"].unique()))
        with c2:
            types = st.multiselect("⚠️ 事件類別", sorted(df["事件類別"].unique()), default=sorted(df["事件類別"].unique()))
        with c3:
            depts = st.multiselect("🏢 發生單位", sorted(df["發生單位"].unique()), default=sorted(df["發生單位"].unique()))
        with c4:
            if st.button("🔄 重置篩選", use_container_width=True):
                st.session_state.selected_event = None
                st.session_state.selected_dept = None
                st.session_state.selected_year = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        f_df = df[(df["年度"].isin(years)) & (df["事件類別"].isin(types)) & (df["發生單位"].isin(depts))]

        # --- KPI 卡片 (專業儀表板風格) ---
        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        
        total_cases = len(f_df)
        k1.metric("📊 總案件數", f"{total_cases:,}", delta=None)
        
        if not f_df.empty and "事件類別" in f_df.columns and not f_df["事件類別"].mode().empty:
            main_risk = f_df["事件類別"].mode()[0]
            risk_count = len(f_df[f_df["事件類別"] == main_risk])
            k2.metric("⚠️ 主要風險", main_risk, delta=f"{risk_count} 件")
        else:
            k2.metric("⚠️ 主要風險", "-", delta=None)
        
        percentage = round(len(f_df)/len(df)*100, 1) if not df.empty else 0
        k3.metric("📈 篩選佔比", f"{percentage}%", delta=f"{len(df)} 件總數")
        
        k4.metric("📅 監測年度", f"{len(years)}", delta="個年度")
        
        if not f_df.empty and "發生單位" in f_df.columns:
            unique_depts = f_df["發生單位"].nunique()
            k5.metric("🏢 涉及單位", f"{unique_depts}", delta="個單位")
        else:
            k5.metric("🏢 涉及單位", "0", delta=None)

        # --- 主要內容區 ---
        tab_total, tab_trend, tab_data, tab_detail = st.tabs(["📌 統計總覽", "📈 趨勢分析", "📋 資料明細", "🔍 點擊詳情"])
        
        with tab_total:
            # 第一行：兩個主要圖表
            col_l, col_r = st.columns([1, 1])
            
            with col_l:
                st.markdown("### 🎯 事件分布比率")
                if not f_df.empty and "事件類別" in f_df.columns:
                    event_counts = f_df["事件類別"].value_counts()
                    fig_pie = px.pie(
                        values=event_counts.values, 
                        names=event_counts.index, 
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>數量: %{value}<br>占比: %{percent}<extra></extra>'
                    )
                    fig_pie.update_layout(
                        showlegend=True, 
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=400,
                        font=dict(size=12)
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
                            st.rerun()
                    
                    # 快速選擇按鈕
                    st.markdown("**快速選擇：**")
                    quick_cols = st.columns(min(5, len(event_counts)))
                    for idx, (event_name, count) in enumerate(event_counts.head(5).items()):
                        with quick_cols[idx % len(quick_cols)]:
                            if st.button(f"{event_name}\n({count})", key=f"pie_btn_{event_name}", use_container_width=True):
                                st.session_state.selected_event = event_name
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
                        color_continuous_scale='Blues'
                    )
                    fig_bar.update_traces(
                        hovertemplate='<b>%{y}</b><br>案件數: %{x}<extra></extra>'
                    )
                    fig_bar.update_layout(
                        showlegend=False, 
                        yaxis={'categoryorder':'total ascending'},
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=400,
                        xaxis_title="案件數量",
                        yaxis_title=""
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
                            st.rerun()
                    
                    # 快速選擇按鈕
                    st.markdown("**快速選擇：**")
                    quick_cols = st.columns(min(5, len(dept_rank)))
                    for idx, row in dept_rank.head(5).iterrows():
                        with quick_cols[idx % len(quick_cols)]:
                            if st.button(f"{row['發生單位']}\n({row['count']})", key=f"bar_btn_{row['發生單位']}", use_container_width=True):
                                st.session_state.selected_dept = row['發生單位']
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
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=350,
                        xaxis_title="年度",
                        yaxis_title="案件數量"
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
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=350,
                        xaxis_title="事件類別",
                        yaxis_title="案件數量",
                        xaxis_tickangle=-45
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
                        margin=dict(t=50, b=50, l=50, r=50),
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
                
                st.dataframe(
                    f_df[final_cols], 
                    use_container_width=True, 
                    height=500,
                    hide_index=True
                )
            else:
                st.warning("目前篩選條件下無資料可顯示")
        
        with tab_detail:
            st.markdown("### 🔍 圖表點擊詳情")
            st.markdown("**提示：** 點擊上方圖表中的資料點，下方會自動顯示對應的詳細資料")
            
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
                st.dataframe(
                    detail_df[available_cols],
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                # 下載按鈕
                csv_detail = detail_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 下載此篩選結果 (CSV)", 
                    csv_detail, 
                    f"detail_{st.session_state.selected_event or 'data'}.csv", 
                    "text/csv"
                )
            else:
                st.info("👆 請點擊上方圖表中的資料點來查看詳細資訊")
                
                # 顯示快速篩選
                st.markdown("---")
                st.markdown("#### 🎯 快速篩選預覽")
                quick_col1, quick_col2 = st.columns(2)
                
                with quick_col1:
                    if not f_df.empty and "事件類別" in f_df.columns:
                        st.markdown("**事件類別快速選擇：**")
                        event_list = sorted(f_df["事件類別"].unique())
                        for event in event_list[:10]:  # 顯示前10個
                            if st.button(f"📌 {event}", key=f"quick_event_{event}", use_container_width=True):
                                st.session_state.selected_event = event
                                st.rerun()
                
                with quick_col2:
                    if not f_df.empty and "發生單位" in f_df.columns:
                        st.markdown("**單位快速選擇：**")
                        dept_list = sorted(f_df["發生單位"].unique())
                        for dept in dept_list[:10]:  # 顯示前10個
                            if st.button(f"🏢 {dept}", key=f"quick_dept_{dept}", use_container_width=True):
                                st.session_state.selected_dept = dept
                                st.rerun()
    
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
