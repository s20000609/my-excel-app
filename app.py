import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 頁面設定 ---
st.set_page_config(page_title="異常事件戰情室 V7", layout="wide", page_icon="📈")

# --- 自定義 CSS (仿六版 HTML 風格) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        font-size: 16px;
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
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
st.title("📊 114 異常事件分析儀表板")
st.caption("數據驅動決策 · 異常事件即時監測系統")

uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:
    with st.spinner("正在讀取和分析 Excel 檔案..."):
        df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        # --- 頂部篩選區 (一橫排，直覺化) ---
        st.write("### 🔍 快速篩選")
        c1, c2, c3 = st.columns(3)
        with c1:
            years = st.multiselect("📅 年度", df["年度"].unique(), default=df["年度"].unique())
        with c2:
            types = st.multiselect("⚠️ 類別", df["事件類別"].unique(), default=df["事件類別"].unique())
        with c3:
            depts = st.multiselect("🏢 單位", df["發生單位"].unique(), default=df["發生單位"].unique())
        
        f_df = df[(df["年度"].isin(years)) & (df["事件類別"].isin(types)) & (df["發生單位"].isin(depts))]

        # --- KPI 卡片 (仿六版視覺) ---
        st.write("---")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("總案件數", f"{len(f_df)} 件")
        if not f_df.empty and "事件類別" in f_df.columns and not f_df["事件類別"].mode().empty:
            k2.metric("主要風險", f_df["事件類別"].mode()[0])
        else:
            k2.metric("主要風險", "-")
        k3.metric("本期佔比", f"{round(len(f_df)/len(df)*100, 1)}%" if not df.empty else "0%")
        k4.metric("監測年度", f"{len(years)} 年")

        # --- 主要內容區 ---
        tab_total, tab_trend, tab_data = st.tabs(["📌 統計總覽", "📈 趨勢分析", "📋 資料明細"])
        
        with tab_total:
            col_l, col_r = st.columns([1, 1])
            with col_l:
                st.subheader("事件分布比率")
                fig_pie = px.pie(f_df, names="事件類別", hole=0.5, 
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_r:
                st.subheader("單位發生次數排名")
                if "發生單位" in f_df.columns and not f_df["發生單位"].empty:
                    dept_rank = f_df["發生單位"].value_counts().reset_index()
                    dept_rank.columns = ["發生單位", "count"]
                    dept_rank = dept_rank.head(10)
                    fig_bar = px.bar(dept_rank, x="count", y="發生單位", orientation='h', 
                                     text="count", color="count", color_continuous_scale='Blues')
                    fig_bar.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("無資料可顯示")

        with tab_trend:
            st.subheader("跨年度案件趨勢")
            if not f_df.empty and "年度" in f_df.columns and "事件類別" in f_df.columns:
                trend = f_df.groupby(["年度", "事件類別"]).size().reset_index(name="件數")
                if not trend.empty:
                    fig_trend = px.line(trend, x="年度", y="件數", color="事件類別", markers=True)
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("無資料可顯示")
            else:
                st.info("無資料可顯示")

        with tab_data:
            st.subheader("原始事件清單")
            st.dataframe(f_df, use_container_width=True, height=400)
            
            # 提供 CSV 下載按鈕
            if not f_df.empty:
                csv = f_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載篩選後的資料 (CSV)", csv, "filtered_data.csv", "text/csv")
            else:
                st.warning("目前篩選條件下無資料可下載")
    
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
