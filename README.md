# 🌺 Okinawa Spectrum Logger

沖縄フィールドワークのための体験記録・可視化アプリです。  
訪問先の「ハード（物質・環境）」と「ソフト（情報・体験）」を2軸で評価し、散布図・地図・ベクトル分析で可視化します。

## ✨ Features

- 📍 **地図表示** — 訪問地点を Folium 地図上にマッピング
- 📊 **2軸スペクトル分析** — 真正性×感情の散布図（ハード/ソフト別）
- 🏹 **統合ベクトル分析** — ハード→ソフトの変化を矢印で可視化
- 📸 **写真アップロード** — 現地写真を記録に添付
- 💾 **CSV 自動保存** — 記録データを CSV に自動保存

## 🚀 Setup

### 1. リポジトリをクローン

```bash
git clone https://github.com/daigo1302-gif/okinawa_app.git
cd okinawa_app
```

### 2. Python 仮想環境を作成（推奨）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. アプリを起動

```bash
streamlit run app.py
```

または Windows の場合は `start.bat` をダブルクリックしてください。

## 📁 Project Structure

```
okinawa_app/
├── app.py                # メインアプリケーション
├── requirements.txt      # Python 依存パッケージ
├── start.bat             # Windows 起動スクリプト
├── photos/               # アップロード写真の保存先
└── README.md
```

## 📝 License

MIT
