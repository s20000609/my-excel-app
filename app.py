import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="異常事件趨勢分析", layout="wide")
st.title("🏥 異常事件跨年度分析整合系統")
st.markdown("此工具會自動偵測標題列並合併不同年度的 Excel 表單。")

# 1. 定義智慧讀取函數
def load_and_standardize(file):
    xl = pd.ExcelFile(file)
    all_data = []
    
    # 定義欄位同義詞字典 (統一欄位名稱)
    rename_map = {
        "發生部門": "發生單位",
        "事件發生地點": "發生地點",
        "通報部門": "通報單位",
        # 根據需要可以繼續新增
    }

    for sheet in xl.sheet_names:
        # 先讀取前 20 行來尋找標題列在哪裡
        # 預設 header=None 先全讀進來找關鍵字
        df_temp = pd.read_excel(file, sheet_name=sheet, header=None, nrows=20)
        
        header_row_index = -1
        # 尋找包含 "單號" 或 "通報日期" 的那一列
        for i, row in df_temp.iterrows():
            row_values = row.astype(str).values
            if "單號" in row_values or "通報日期" in row_values:
                header_row_index = i
                break
        
        if header_row_index != -1:
            # 找到標題列後，正式讀取該 sheet
            df = pd.read_excel(file, sheet_name=sheet, header=header_row_index)
            
            # 統一欄位名稱
            df.rename(columns=rename_map, inplace=True)
            
            # 加入一個「年度/表單」欄位，方便後續篩選
            df["來源表單"] = sheet
            
            # 確保必要的欄位存在 (避免空表單報錯)
            if "事件類別" in df.columns:
                all_data.append(df)
        else:
            st.warning(f"⚠️ 在表單 '{sheet}' 中找不到標準標題列，已跳過。")

    if all_data:
        # 合併所有 DataFrame
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df
    else:
        return None

# 2. 檔案上傳區
uploaded_file = st.file_uploader("📂 請上傳 Excel 檔案 (包含多個年度)", type=["xlsx"])

if uploaded_file:
    with st.spinner('正在進行智慧合併與資料清理...'):
        df = load_and_standardize(uploaded_file)
    
    if df is not None:
        st.success(f"成功合併！共讀取 {len(df)} 筆資料，來自 {df['來源表單'].nunique()} 個表單。")
        
        # 3. 側邊欄：全域篩選
        st.sidebar.header("🔍 資料篩選")
        
        # 年度篩選
        all_sheets = df["來源表單"].unique().tolist()
        selected_sheets = st.sidebar.multiselect("選擇年度/來源", all_sheets, default=all_sheets)
        
        # 事件類別篩選
        if "事件類別" in df.columns:
            all_types = df["事件類別"].astype(str).unique().tolist()
            selected_types = st.sidebar.multiselect("選擇事件類別", all_types, default=all_types)
        else:
            selected_types = []
            
        # 執行篩選
        mask = df["來源表單"].isin(selected_sheets)
        if "事件類別" in df.columns and selected_types:
            mask = mask & df["事件類別"].isin(selected_types)
            
        filtered_df = df[mask]
        
        # 4. 視覺化儀表板
        
        # 上半部：關鍵指標
        col1, col2, col3 = st.columns(3)
        col1.metric("總案件數", len(filtered_df))
        if "事件類別" in filtered_df.columns:
            top_event = filtered_df["事件類別"].value_counts().idxmax() if not filtered_df.empty else "無"
            col2.metric("發生最多類別", top_event)
        
        st.divider()

        # 圖表區
        tab1, tab2 = st.tabs(["📊 類別統計", "📅 年度趨勢比較"])
        
        with tab1:
            if "事件類別" in filtered_df.columns and "發生單位" in filtered_df.columns:
                st.subheader("各單位異常事件分佈")
                fig_bar = px.bar(
                    filtered_df, 
                    x="發生單位", 
                    color="事件類別", 
                    title="各單位事件類型堆疊圖",
                    barmode="group"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            st.subheader("跨年度案件量比較")
            # 這裡簡單計算每個來源表單的案件量
            trend_data = filtered_df.groupby(["來源表單", "事件類別"]).size().reset_index(name="案件數")
            fig_line = px.line(
                trend_data, 
                x="來源表單", 
                y="案件數", 
                color="事件類別", 
                markers=True,
                title="各類別事件跨年度變化"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        # 顯示詳細資料
        with st.expander("查看詳細資料表"):
            st.dataframe(filtered_df)
            
    else:
        st.error("無法讀取資料，請確認 Excel 中包含「單號」或「通報日期」等欄位。")