import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="異常事件戰情儀表板", layout="wide", page_icon="🏥")

# --- CSS樣式優化 (讓指標卡片好看一點) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("🏥 異常事件監測儀表板")
st.markdown("跨年度 (111-114) 數據整合分析系統")

# --- 1. 核心處理邏輯 ---
def load_and_clean_data(file):
    xl = pd.ExcelFile(file)
    all_data = []
    
    # 定義更強大的欄位對照表 (左邊是Excel可能出現的字，右邊是統一的名稱)
    rename_map = {
        "新事件類別": "事件類別",  # 這是導致掉資料的主因
        "發生部門": "發生單位",
        "事件發生地點": "發生地點",
        "通報部門": "通報單位",
        "事情發生後受影響的對象": "受影響對象",
        "事件發生後受影響的對象": "受影響對象",
        "通報日期": "日期"
    }

    logs = [] # 用來記錄讀取狀況給使用者看

    for sheet in xl.sheet_names:
        # 讀取前 30 行找標題 (放寬範圍)
        df_temp = pd.read_excel(file, sheet_name=sheet, header=None, nrows=30)
        
        header_row_index = -1
        # 尋找關鍵字
        for i, row in df_temp.iterrows():
            row_str = row.astype(str).values
            if "單號" in row_str or "通報員編" in row_str:
                header_row_index = i
                break
        
        if header_row_index != -1:
            # 正式讀取
            df = pd.read_excel(file, sheet_name=sheet, header=header_row_index)
            
            # 1. 先改名
            df.rename(columns=rename_map, inplace=True)
            
            # 2. 標記來源
            df["年度"] = sheet
            
            # 3. 確保關鍵欄位存在，若無則補空值 (避免報錯)
            if "事件類別" not in df.columns:
                df["事件類別"] = "未分類"
            if "發生單位" not in df.columns:
                df["發生單位"] = "未知單位"
                
            all_data.append(df)
            logs.append(f"✅ 成功讀取表單：{sheet} (共 {len(df)} 筆)")
        else:
            logs.append(f"⚠️ 跳過表單：{sheet} (找不到標題列)")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # --- 資料清洗與型別轉換 ---
        # 處理日期格式 (將文字轉為 datetime)
        final_df["日期"] = pd.to_datetime(final_df["日期"], errors='coerce')
        final_df["月份"] = final_df["日期"].dt.strftime('%Y-%m') # 轉成年-月字串
        final_df["年"] = final_df["日期"].dt.year
        
        return final_df, logs
    else:
        return None, logs

# --- 2. 介面呈現 ---
uploaded_file = st.file_uploader("📂 上傳整合 Excel (支援多Sheet)", type=["xlsx"])

if uploaded_file:
    df, logs = load_and_clean_data(uploaded_file)
    
    # 顯示讀取日誌 (讓你知道每一張表有沒有抓到)
    with st.expander("查看資料讀取狀態"):
        for log in logs:
            st.write(log)
        if df is not None:
            st.write(f"📊 **總計合併資料筆數：{len(df)} 筆**")

    if df is not None:
        st.divider()
        
        # --- 側邊欄篩選 ---
        st.sidebar.header("🔍 篩選條件")
        
        # 年份篩選
        years = sorted(df["年度"].unique().tolist())
        selected_years = st.sidebar.multiselect("選擇年度", years, default=years)
        
        # 單位篩選
        depts = df["發生單位"].astype(str).unique().tolist()
        selected_depts = st.sidebar.multiselect("選擇發生單位", depts, default=depts)

        # 類別篩選
        types = df["事件類別"].astype(str).unique().tolist()
        selected_types = st.sidebar.multiselect("選擇事件類別", types, default=types)

        # 執行篩選
        mask = (df["年度"].isin(selected_years)) & \
               (df["發生單位"].isin(selected_depts)) & \
               (df["事件類別"].isin(selected_types))
        filtered_df = df[mask]

        # --- 3. 儀表板 KPI 區 (Dashboard Header) ---
        col1, col2, col3, col4 = st.columns(4)
        
        total_cases = len(filtered_df)
        
        # 計算最常發生的類別
        top_type = filtered_df["事件類別"].mode()[0] if not filtered_df.empty else "無"
        top_type_count = filtered_df["事件類別"].value_counts().max() if not filtered_df.empty else 0
        
        # 計算最常發生的單位
        top_dept = filtered_df["發生單位"].mode()[0] if not filtered_df.empty else "無"
        
        # 嚴重度統計 (假設有 '影響程度' 欄位，若無則顯示 N/A)
        # 這裡根據你的檔案欄位做個容錯
        severity_col = "受影響對象" if "受影響對象" in filtered_df.columns else None
        top_victim = filtered_df[severity_col].mode()[0] if (severity_col and not filtered_df.empty) else "未知"

        col1.metric("📌 總案件數", f"{total_cases} 件")
        col2.metric("⚠️ 最高頻事件", f"{top_type}", f"{top_type_count} 件")
        col3.metric("🏥 熱點單位", f"{top_dept}")
        col4.metric("🤕 主要影響對象", f"{top_victim}")

        st.markdown("---")

        # --- 4. 圖表區 (兩欄佈局) ---
        
        # Row 1: 圓餅圖 + 長條圖
        c1, c2 = st.columns([1, 2]) # 左窄右寬
        
        with c1:
            st.subheader("事件類別佔比")
            if not filtered_df.empty:
                fig_pie = px.pie(filtered_df, names="事件類別", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            st.subheader("各單位發生次數排名")
            if not filtered_df.empty:
                dept_counts = filtered_df["發生單位"].value_counts().reset_index()
                dept_counts.columns = ["發生單位", "次數"]
                fig_bar = px.bar(dept_counts.head(10), x="發生單位", y="次數", text="次數", color="次數")
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

        # Row 2: 趨勢圖 (折線圖)
        st.subheader("📅 案件發生時間趨勢")
        if not filtered_df.empty and "日期" in filtered_df.columns:
            # 依月份+類別統計
            trend_df = filtered_df.groupby([pd.Grouper(key='日期', freq='M'), '事件類別']).size().reset_index(name='件數')
            fig_line = px.line(trend_df, x="日期", y="件數", color="事件類別", markers=True)
            fig_line.update_layout(xaxis_title="時間", yaxis_title="案件數")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("無法解析日期欄位，請確認 Excel 包含 '通報日期' 或 '日期' 欄位。")

        # --- 5. 資料明細 ---
        with st.expander("📂 檢視原始資料清單"):
            st.dataframe(filtered_df.sort_values(by="日期", ascending=False), use_container_width=True)

else:
    st.info("👈 請從左側或上方上傳您的 Excel 檔案以開始分析")
