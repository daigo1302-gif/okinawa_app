import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- Google Sheets 連携 ---
GSHEET_ENABLED = False
gsheet_worksheet = None

try:
    import gspread
    from google.oauth2.service_account import Credentials

    if "gcp_service_account" in st.secrets:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(st.secrets["spreadsheet"]["name"])
        gsheet_worksheet = spreadsheet.sheet1
        GSHEET_ENABLED = True
except Exception as e:
    # Google Sheets未設定の場合はCSVフォールバック
    pass


def load_from_gsheet():
    """Google Sheetsから全データを読み込む"""
    try:
        records = gsheet_worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            df = df.fillna("")
            return df.to_dict("records")
        return []
    except Exception:
        return []


def save_to_gsheet(log_entry):
    """Google Sheetsに1行追加する"""
    try:
        # ヘッダーが無ければ追加
        existing = gsheet_worksheet.get_all_values()
        headers = [
            "Location", "Hard_Y_Authenticity", "Hard_X_Affect",
            "Soft_Y_Correctness", "Soft_X_Affect",
            "Comment", "Image_Path", "Timestamp"
        ]
        if not existing:
            gsheet_worksheet.append_row(headers)

        row = [
            log_entry.get("Location", ""),
            log_entry.get("Hard_Y_Authenticity", 0),
            log_entry.get("Hard_X_Affect", 0),
            log_entry.get("Soft_Y_Correctness", 0),
            log_entry.get("Soft_X_Affect", 0),
            log_entry.get("Comment", ""),
            log_entry.get("Image_Path", ""),
            log_entry.get("Timestamp", ""),
        ]
        gsheet_worksheet.append_row(row)
        return True
    except Exception:
        return False


def delete_from_gsheet(row_index):
    """Google Sheetsから行を削除する (row_index: 0-based, ヘッダー除く)"""
    try:
        # gspreadは1-based, ヘッダーが1行目なので +2
        gsheet_worksheet.delete_rows(row_index + 2)
        return True
    except Exception:
        return False


# ページ設定
st.set_page_config(page_title="Okinawa Spectrum Logger", layout="wide")

st.title("🌺 Okinawa Spectrum Logger (All-in-One Analysis)")

# データソース表示
if GSHEET_ENABLED:
    st.caption("☁️ Google Sheets に接続中 — データはリアルタイムで共有されます")
else:
    st.caption("💾 ローカルCSVモード — Google Sheets未設定")

# 座標データの定義
LAT_LON = {
    "アメリカンビレッジ (北谷)": [26.316, 127.756],
    "ピザハウス (夕食)": [26.262, 127.733],
    "むら咲むら (読谷)": [26.406, 127.718],
    "ホテル日航アリビラ (ランチ)": [26.413, 127.715],
    "座喜味城跡 (読谷)": [26.408, 127.742],
    "佐喜眞美術館 (宜野湾)": [26.273, 127.754],
    "那覇港・フェリー (海上)": [26.216, 127.674]
}

# セッション状態の初期化
if 'logs' not in st.session_state:
    if GSHEET_ENABLED:
        st.session_state.logs = load_from_gsheet()
    elif os.path.exists("okinawa_survey_data.csv"):
        try:
            df_load = pd.read_csv("okinawa_survey_data.csv")
            df_load = df_load.fillna("") 
            st.session_state.logs = df_load.to_dict('records')
        except pd.errors.EmptyDataError:
            st.session_state.logs = []
    else:
        st.session_state.logs = []

# Google Sheets接続時は毎回最新データを取得
if GSHEET_ENABLED:
    st.session_state.logs = load_from_gsheet()

# --- サイドバー（入力画面） ---
with st.sidebar:
    st.header("Record Field Work")
    locations = list(LAT_LON.keys())
    option = st.selectbox("場所 (Location)", locations + ["その他 (自由入力)"])
    
    if option == "その他 (自由入力)":
        location = st.text_input("場所名を入力してください", "名もなきグスク")
    else:
        location = option

    # --- ハード（物質・環境）の評価 ---
    st.subheader("🟥 ハード (Start: 器・環境)")
    st.caption("建物、遺構、インフラ、景観について")
    h_y_val = st.slider("H-Y軸: 偽 (Replica) ↔ 真 (Original)", -50, 50, 0, key="h_y")
    h_x_val = st.slider("H-X軸: 苦 (Decay/Harsh) ↔ 快 (Comfort)", -50, 50, 0, key="h_x")

    # --- ソフト（情報・体験）の評価 ---
    st.subheader("🟦 ソフト (End: 中身・情報)")
    st.caption("展示、ガイド、ストーリー、正当性について")
    s_y_val = st.slider("S-Y軸: 誤 (Fiction/Error) ↔ 正 (Fact/Correct)", -50, 50, 0, key="s_y")
    s_x_val = st.slider("S-X軸: 苦 (Painful story) ↔ 快 (Fun/Entertainment)", -50, 50, 0, key="s_x")

    uploaded_file = st.file_uploader("写真 (Photo)", type=['png', 'jpg', 'jpeg'])
    comment = st.text_area("コメント (Comment)", height=100)

    if st.button("記録する (Record)"):
        save_dir = "photos"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        saved_photo_path = ""
        if uploaded_file is not None:
            file_extension = os.path.splitext(uploaded_file.name)[1]
            file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            saved_photo_path = os.path.join(save_dir, file_name)
            with open(saved_photo_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        new_log = {
            "Location": location,
            "Hard_Y_Authenticity": h_y_val,
            "Hard_X_Affect": h_x_val,
            "Soft_Y_Correctness": s_y_val,
            "Soft_X_Affect": s_x_val,
            "Comment": comment,
            "Image_Path": saved_photo_path,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.logs.append(new_log)

        if GSHEET_ENABLED:
            save_to_gsheet(new_log)
        
        # CSVにも保存（バックアップ）
        pd.DataFrame(st.session_state.logs).to_csv("okinawa_survey_data.csv", index=False, encoding="utf-8-sig")
        st.success("記録完了！")
        st.rerun()

# --- メイン画面（可視化） ---
if st.session_state.logs:
    # 画面を左(地図)と右(グラフ群)に分割
    col_map_side, col_graphs_side = st.columns([1, 2.5])

    # === 左側：地図 ===
    with col_map_side:
        st.subheader("📍 Field Map")
        m = folium.Map(location=[26.3, 127.75], zoom_start=9)
        for log in st.session_state.logs:
            if log['Location'] in LAT_LON:
                # 地図ピンはハード（物質）の真正性で色分け
                icon_color = "blue" if log.get('Hard_Y_Authenticity', 0) >= 0 else "red"
                folium.Marker(
                    location=LAT_LON[log['Location']],
                    popup=f"{log['Location']}",
                    tooltip=log['Location'],
                    icon=folium.Icon(color=icon_color, icon="info-sign")
                ).add_to(m)
        st_folium(m, height=600, width=None) # 高さをグラフ群に合わせる

    # === 右側：グラフ群 ===
    with col_graphs_side:
        df = pd.DataFrame(st.session_state.logs)
        
        # 数値型に変換（Google Sheetsから文字列で来る場合の対策）
        for col in ["Hard_Y_Authenticity", "Hard_X_Affect", "Soft_Y_Correctness", "Soft_X_Affect"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # --- 上段：個別分析グラフ（左右分割） ---
        col_hard_g, col_soft_g = st.columns(2)
        
        # 🟥 ハード図
        with col_hard_g:
            st.subheader("🟥 ハード (器・環境)")
            fig_h = px.scatter(
                df, x="Hard_X_Affect", y="Hard_Y_Authenticity", text="Location",
                range_x=[-60,60], range_y=[-60,60], height=350,
                labels={"Hard_X_Affect": "環境的快苦 (苦↔快)", "Hard_Y_Authenticity": "物質的真正性 (偽↔真)"}
            )
            fig_h.update_traces(marker=dict(size=12, color='firebrick', line=dict(width=1, color='DarkSlateGrey')), textposition='top center')
            fig_h.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_h.add_vline(x=0, line_dash="dash", line_color="gray")
            fig_h.update_layout(plot_bgcolor="rgba(255, 240, 240, 0.5)", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_h, use_container_width=True)

        # 🟦 ソフト図
        with col_soft_g:
            st.subheader("🟦 ソフト (中身・情報)")
            fig_s = px.scatter(
                df, x="Soft_X_Affect", y="Soft_Y_Correctness", text="Location",
                range_x=[-60,60], range_y=[-60,60], height=350,
                labels={"Soft_X_Affect": "体験的感情 (苦↔快)", "Soft_Y_Correctness": "史実的正確性 (誤↔正)"}
            )
            fig_s.update_traces(marker=dict(size=12, color='royalblue', line=dict(width=1, color='DarkSlateGrey')), textposition='top center')
            fig_s.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_s.add_vline(x=0, line_dash="dash", line_color="gray")
            fig_s.update_layout(plot_bgcolor="rgba(240, 240, 255, 0.5)", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_s, use_container_width=True)
            
        st.write("---") # 区切り線

        # --- 下段：統合ベクトル分析グラフ ---
        st.subheader("🏹 統合ベクトル分析 (Hard → Soft)")
        st.caption("赤丸(物質)から青丸(体験)への「矢印」が、演出による変化の軌跡を表します。")
        
        fig_v = go.Figure()
        fig_v.update_layout(
            xaxis=dict(title="感情 (苦/Pain ↔ 快/Fun)", range=[-60, 60], zeroline=True, zerolinewidth=1, zerolinecolor='gray'),
            yaxis=dict(title="真実性 (偽・誤/Fake ↔ 真・正/True)", range=[-60, 60], zeroline=True, zerolinewidth=1, zerolinecolor='gray'),
            plot_bgcolor="rgba(245,245,245,1)", height=500,
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # 凡例を上に見やすく配置
        )

        for i, log in enumerate(st.session_state.logs):
            h_x = float(log.get('Hard_X_Affect', 0) or 0)
            h_y = float(log.get('Hard_Y_Authenticity', 0) or 0)
            s_x = float(log.get('Soft_X_Affect', 0) or 0)
            s_y = float(log.get('Soft_Y_Correctness', 0) or 0)
            
            # 矢印
            fig_v.add_annotation(
                x=s_x, y=s_y,
                ax=h_x, ay=h_y,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor="rgba(100,100,100,0.6)"
            )
            # ハード点（赤）
            fig_v.add_trace(go.Scatter(
                x=[h_x], y=[h_y],
                mode='markers', marker=dict(color='firebrick', size=10, line=dict(width=1, color='DarkSlateGrey')),
                name='Hard (物質)' if i == 0 else None, showlegend=(i == 0),
                hovertext=f"{log['Location']} (Hard)"
            ))
            # ソフト点（青）
            fig_v.add_trace(go.Scatter(
                x=[s_x], y=[s_y],
                mode='markers+text', marker=dict(color='royalblue', size=12, line=dict(width=1, color='DarkSlateGrey')),
                text=[log['Location']], textposition="top center",
                name='Soft (体験)' if i == 0 else None, showlegend=(i == 0),
                hovertext=f"{log['Location']} (Soft)"
            ))

        st.plotly_chart(fig_v, use_container_width=True)

    # === 最下部：記録リスト ===
    st.write("---")
    st.subheader("📜 Records List")
    for i in range(len(st.session_state.logs) - 1, -1, -1):
        log = st.session_state.logs[i]
        with st.expander(f"【{log['Location']}】 ({log['Timestamp']})"):
            c1, c2 = st.columns([1, 3])
            with c1:
                img_path = log.get("Image_Path", "")
                if img_path and isinstance(img_path, str) and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                if st.button(f"🗑️ 削除", key=f"del_{i}"):
                    if img_path and isinstance(img_path, str) and os.path.exists(img_path):
                        os.remove(img_path)
                    
                    if GSHEET_ENABLED:
                        delete_from_gsheet(i)
                    
                    st.session_state.logs.pop(i)
                    pd.DataFrame(st.session_state.logs).to_csv("okinawa_survey_data.csv", index=False, encoding="utf-8-sig")
                    st.rerun()
            with c2:
                col_h_s, col_s_s = st.columns(2)
                with col_h_s:
                    st.markdown("##### 🟥 Hard Status")
                    st.write(f"真正性(Y): `{log.get('Hard_Y_Authenticity', 0)}`")
                    st.write(f"感情(X): `{log.get('Hard_X_Affect', 0)}`")
                with col_s_s:
                    st.markdown("##### 🟦 Soft Status")
                    st.write(f"正確性(Y): `{log.get('Soft_Y_Correctness', 0)}`")
                    st.write(f"感情(X): `{log.get('Soft_X_Affect', 0)}`")
                st.info(f"**📝 コメント:**\n{log['Comment']}")
else:
    st.info("← 左側のサイドバーから、最初の調査記録を追加してください。")