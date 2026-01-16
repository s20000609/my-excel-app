import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="醫院異常事件儀表板", layout="wide", page_icon="🏥")

st.title("🏥 異常事件監測戰情室")
st.markdown("已修正欄位重複衝突，支援 111-114 年全數據整合")

def load_and_clean_data(file):
    xl = pd.ExcelFile(file)
    all_data = []
    logs = []

    for sheet in xl.sheet_names:
        # 讀取前 25 行找標題
        df_temp = pd.read_excel(file, sheet_name=sheet, header=None, nrows=25)
        
        header_row_index = -1
        for i, row in df_temp.iterrows():
            row_str = [str(x) for x in row.values]
            if "單號" in row_str or "通報日期" in row_str:
                header_row_index = i
                break
        
        if header_row_index != -1:
            # 正式讀取該頁
            df = pd.read_excel(file, sheet_name=sheet, header=header_row_index)
            
            # --- 核心修正：處理重複欄位 ---
            # 1. 移除全空的欄位
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            # 2. 如果有重複的欄位名，只保留第一個
            df = df.loc[:, ~df.columns.duplicated()]
            
            # --- 欄位正規化 ---
            # 優先檢查「新事件類別」，如果存在就把它當作「事件類別」
            if "新事件類別" in df.columns:
                df["事件類別"] = df["新事件類別"]
            
            # 統一其他常見名稱
            rename_dict = {
                "發生部門": "發生單位",
                "發生部門 ": "發生單位",
                "事件發生地點": "發生地點",
                "事情發生後受影響的對象": "受影響對象",
                "通報日期": "日期"
            }
            df.rename(columns=rename_dict, inplace=True)
            
            # 確保有必要的欄位
            if "日期" not in df.columns:
                df["日期"] = pd.NaT
            if "事件類別" not in df.columns:
                df["事件類別"] = "未知類別"
            if "發生單位" not in df.columns:
                df["發生單位"] = "10F病房" # 預設補值
            
            # 只取我們需要的關鍵欄位，避免其他雜亂欄位干擾合併
            needed_cols = ["單號", "日期", "事件類別", "發生單位", "發生地點", "受影響對象", "事件描述"]
            existing_cols = [c for c in needed_cols if c in df.columns]
            df_final = df[existing_cols].copy()
            df_final["年度來源"] = sheet
            
            all_data.append(df_final)
            logs.append(f"✅ {sheet}：讀取成功 ({len(df_final)} 筆)")
        else:
            logs.append(f"⚠️ {sheet}：找不到標題列 (關鍵字：單號)")

    if all_data:
        # 合併時強制不檢查索引，解決 InvalidIndexError
        final_df = pd.concat(all_data, axis=0, ignore_index=True)
        # 清理日期
        final_df["日期"] = pd.to_datetime(final_df["日期"], errors='coerce')
        return final_df, logs
    return None, logs

uploaded_file = st.file_uploader("📂 上傳 Excel 檔案", type=["xlsx"])

if uploaded_file:
    df, logs = load_and_clean_data(uploaded_file)
    
    with st.expander("📝 資料匯入日誌"):
        for l in logs: st.write(l)

    if df is not None:
        # --- 儀表板設計 ---
        st.divider()
        
        # 側邊欄篩選
        st.sidebar.header("篩選器")
        sel_year = st.sidebar.multiselect("年度", df["年度來源"].unique(), default=df["年度來源"].unique())
        sel_type = st.sidebar.multiselect("事件類別", df["事件類別"].unique(), default=df["事件類別"].unique())
        
        f_df = df[(df["年度來源"].isin(sel_year)) & (df["事件類別"].isin(sel_type))]

        # KPI 卡片
        c1, c2, c3 = st.columns(3)
        c1.metric("總案件量", f"{len(f_df)} 件")
        if not f_df.empty:
            c2.metric("主要類別", f_df["事件類別"].mode()[0])
            c3.metric("本月新增", len(f_df[f_df["日期"] >= pd.Timestamp.now().replace(day=1)]))

        # 圖表
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("事件分布比率")
            fig1 = px.pie(f_df, names="事件類別", hole=0.3)
            st.plotly_chart(fig1, use_container_width=True)
        with col_r:
            st.subheader("各年度趨勢")
            trend = f_df.groupby("年度來源").size().reset_index(name="件數")
            fig2 = px.bar(trend, x="年度來源", y="件數", text="件數", color="年度來源")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 資料明細 (可點選標題排序)")
        st.dataframe(f_df, use_container_width=True)
