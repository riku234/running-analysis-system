# 検証・データ出力フォルダ

このフォルダは、システム本体とは関係ない検証作業やデータ出力を管理するためのものです。

## 📁 フォルダ構成

```
verification/
├── csv_export/        # CSV出力スクリプト
├── outputs/           # 生成されたCSVファイル等
├── data_analysis/     # データ分析スクリプト
└── README.md          # このファイル
```

## 🔧 csv_export/

CSV生成・出力関連のスクリプトを格納

### 含まれるスクリプト
- `generate_enhanced_csv.py` - 骨格データ + 角度データ + Zスコアを統合したCSV生成

### 使い方
```bash
# Dockerコンテナ内で実行
docker cp verification/csv_export/generate_enhanced_csv.py running-analysis-system-video_processing-1:/app/
docker-compose exec video_processing python3 /app/generate_enhanced_csv.py
```

## 📊 outputs/

生成されたCSVファイルや検証結果を格納

### 現在のファイル
- `enhanced_58bc828c_utf8.csv` - UTF-8エンコード版CSV（全19列）
- `enhanced_58bc828c_sjis.csv` - Shift-JISエンコード版CSV（全19列）
- `enhanced_58bc828c.csv` - 旧バージョン（削除予定）

### CSVの列構成
1-8列: 既存データ（骨格情報）
9-13列: 角度データ（体幹、左右大腿、左右下腿）
14-19列: イベント＆Zスコアデータ

## 🔬 data_analysis/

データ分析・検証用のスクリプトを格納（今後使用予定）

---

**注意**: このフォルダ内のファイルは本番システムには含まれません。
開発・検証目的のみで使用してください。


