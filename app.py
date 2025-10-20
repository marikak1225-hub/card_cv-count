import streamlit as st
import pandas as pd
import os

st.title("広告データ集計ツール")

# AFマスター固定読み込み
af_path = "AFマスター.xlsx"
if not os.path.exists(af_path):
    st.error("AFマスター.xlsxがアプリフォルダにありません。配置してください。")
else:
    af_df = pd.read_excel(af_path, usecols="B:D", header=1)
    af_df.columns = ["AFコード", "媒体", "分類"]

    # testファイルアップロード
    test_file = st.file_uploader("test.xlsxをアップロード", type="xlsx")

    if test_file:
        test_df = pd.read_excel(test_file, header=0)

        # 日付列処理
        test_df["日付"] = pd.to_datetime(test_df.iloc[:, 0], format="%Y%m%d")

        # 日付範囲選択
        min_date = test_df["日付"].min()
        max_date = test_df["日付"].max()
        start_date, end_date = st.date_input("期間を選択", [min_date, max_date])

        filtered = test_df[(test_df["日付"] >= pd.to_datetime(start_date)) & (test_df["日付"] <= pd.to_datetime(end_date))]

        # 突合処理
        mapping = af_df.set_index("AFコード")[["媒体", "分類"]].to_dict("index")
        ad_codes = test_df.columns[1:]  # A列は日付なので除外

        affiliate_prefixes = ["GEN", "AFA", "AFP", "RAA"]

        result_list = []
        for code in ad_codes:
            # Affiliate判定
            if any(code.startswith(prefix) for prefix in affiliate_prefixes):
                media = "Affiliate"
                category = "Affiliate"
            elif code in mapping:
                media = mapping[code]["媒体"]
                category = mapping[code]["分類"]
            else:
                continue

            cv_sum = filtered[code].sum()
            result_list.append({"広告コード": code, "媒体": media, "分類": category, "CV合計": cv_sum})

        result_df = pd.DataFrame(result_list)
        grouped = result_df.groupby(["分類", "媒体"], as_index=False)["CV合計"].sum()

        st.subheader("分類・媒体別集計結果")
        st.dataframe(grouped)

        # ✅ マルチセレクトで条件選択
        st.subheader("条件を選択して合計を確認")
        selected_categories = st.multiselect("分類を選択", grouped["分類"].unique())
        selected_media = st.multiselect("媒体を選択", grouped["媒体"].unique())

        # フィルタリングロジック
        filtered_group = grouped.copy()
        if selected_categories and selected_media:
            filtered_group = filtered_group[
                (filtered_group["分類"].isin(selected_categories)) &
                (filtered_group["媒体"].isin(selected_media))
            ]
        elif selected_categories:  # 分類のみ選択
            filtered_group = filtered_group[filtered_group["分類"].isin(selected_categories)]
        elif selected_media:  # 媒体のみ選択
            filtered_group = filtered_group[filtered_group["媒体"].isin(selected_media)]
        # 両方未選択 → 全体

        # 合計CV
        total_cv = filtered_group["CV合計"].sum()
        st.write(f"選択条件の合計CV： **{total_cv}**")

        # 詳細表示
        st.dataframe(filtered_group)