"""
CSVデータをPostgreSQLデータベースに移行するスクリプト

使用方法:
    python backend/scripts/migrate_csv_to_db.py \
        --csv-dir /path/to/csv/files \
        --csv1 統計モデル検討.csv \
        --csv2 ランニング分類.csv \
        --csv3 コメント紐づけ.csv
"""

import os
import sys
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 1. Z値変数名のマッピング辞書
# ==========================================

# 既存コードから特定した角度名とイベント名
ANGLE_NAMES = {
    '体幹': '体幹角度',
    '体幹角度': '体幹角度',
    '左大腿': '左大腿角度',
    '左大腿角度': '左大腿角度',
    '右大腿': '右大腿角度',
    '右大腿角度': '右大腿角度',
    '左下腿': '左下腿角度',
    '左下腿角度': '左下腿角度',
    '右下腿': '右下腿角度',
    '右下腿角度': '右下腿角度',
}

EVENT_NAMES = {
    '右足接地': 'right_strike',
    '右足離地': 'right_off',
    '左足接地': 'left_strike',
    '左足離地': 'left_off',
    'right_strike': 'right_strike',
    'right_off': 'right_off',
    'left_strike': 'left_strike',
    'left_off': 'left_off',
}

OPERATOR_MAPPING = {
    'より小さい': 'lt',
    'より大きい': 'gt',
    '以下': 'lte',
    '以上': 'gte',
    '等しい': 'eq',
    'lt': 'lt',
    'gt': 'gt',
    'lte': 'lte',
    'gte': 'gte',
    'eq': 'eq',
    '<': 'lt',
    '>': 'gt',
    '<=': 'lte',
    '>=': 'gte',
    '=': 'eq',
}

# ==========================================
# 2. データベース接続
# ==========================================

def get_db_connection():
    """
    PostgreSQLデータベースへの接続を確立
    ローカル環境から実行する場合、ホスト名を自動的に調整
    """
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "app")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    
    if not db_host:
        # DB_HOSTが設定されていない場合は、ローカル環境を想定
        db_host = "localhost"
        print("⚠️  DB_HOSTが設定されていません。localhostを使用します。")
    
    # 接続を試行するホスト名のリスト（優先順位順）
    hosts_to_try = [db_host]
    
    # ローカル環境から実行する場合、Dockerコンテナ名（db）では接続できない
    # そのため、localhostも試行する
    if db_host == "db":
        hosts_to_try.append("localhost")
        print(f"💡 Dockerコンテナ名 'db' が指定されています。")
        print(f"   ローカル環境から実行する場合、'localhost' も試行します。")
    
    # 各ホスト名で接続を試行
    last_error = None
    for host in hosts_to_try:
        try:
            print(f"🔌 データベース接続を試みています...")
            print(f"   ホスト: {host}")
            print(f"   ポート: {db_port}")
            print(f"   データベース: {db_name}")
            print(f"   ユーザー: {db_user}")
            
            connection = psycopg2.connect(
                host=host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                connect_timeout=10
            )
            print(f"✅ データベース接続成功! (ホスト: {host})")
            return connection
        except psycopg2.OperationalError as e:
            last_error = e
            print(f"⚠️  ホスト '{host}' への接続に失敗: {e}")
            if host != hosts_to_try[-1]:
                print(f"   次のホストを試行します...")
                continue
        except Exception as e:
            last_error = e
            print(f"❌ 予期しないエラー: {e}")
            break
    
    # すべての接続試行が失敗した場合
    print(f"\n❌ すべての接続試行が失敗しました。")
    print(f"\n💡 確認事項:")
    print(f"   1. データベースコンテナが起動しているか:")
    print(f"      docker compose ps db")
    print(f"   2. .envファイルの設定を確認:")
    print(f"      DB_HOST=localhost (ローカル環境の場合)")
    print(f"      または DB_HOST=db (Dockerコンテナ内から実行する場合)")
    print(f"   3. ポート5432が使用可能か:")
    print(f"      lsof -i :5432")
    
    raise ConnectionError(f"データベース接続に失敗しました: {last_error}")

# ==========================================
# 3. データベーススキーマ作成
# ==========================================

def create_tables(conn):
    """診断ルールとアドバイステーブルを作成"""
    cursor = conn.cursor()
    
    # 診断ルールテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_rules (
            id SERIAL PRIMARY KEY,
            rule_code VARCHAR(100) UNIQUE NOT NULL,
            rule_name VARCHAR(255) NOT NULL,
            target_event VARCHAR(50),
            -- 'right_strike', 'right_off', 'left_strike', 'left_off', NULL (全イベント)
            target_metric VARCHAR(100) NOT NULL,
            -- '体幹角度', '左大腿角度', '右大腿角度', '左下腿角度', '右下腿角度'
            operator VARCHAR(10) NOT NULL,
            -- 'lt', 'gt', 'lte', 'gte', 'eq'
            threshold FLOAT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            -- 'high', 'medium', 'low'
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # 専門家アドバイステーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expert_advice (
            id SERIAL PRIMARY KEY,
            rule_code VARCHAR(100) NOT NULL,
            issue_name VARCHAR(255) NOT NULL,
            observation TEXT,
            cause TEXT,
            action TEXT,
            drill_name VARCHAR(255),
            drill_url VARCHAR(500),
            additional_notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY (rule_code) REFERENCES diagnosis_rules(rule_code) ON DELETE CASCADE
        );
    """)
    
    # インデックスの作成
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_code ON diagnosis_rules(rule_code);
        CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_metric ON diagnosis_rules(target_metric);
        CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_event ON diagnosis_rules(target_event);
        CREATE INDEX IF NOT EXISTS idx_expert_advice_rule_code ON expert_advice(rule_code);
    """)
    
    conn.commit()
    cursor.close()
    print("✅ テーブル作成完了!")

# ==========================================
# 4. CSVデータの読み込みと正規化
# ==========================================

def normalize_angle_name(angle_str: str) -> Optional[str]:
    """角度名を正規化"""
    if pd.isna(angle_str) or not angle_str:
        return None
    angle_str = str(angle_str).strip()
    return ANGLE_NAMES.get(angle_str, angle_str)

def normalize_event_name(event_str: str) -> Optional[str]:
    """イベント名を正規化"""
    if pd.isna(event_str) or not event_str:
        return None
    event_str = str(event_str).strip()
    return EVENT_NAMES.get(event_str, event_str)

def normalize_operator(operator_str: str) -> Optional[str]:
    """演算子を正規化"""
    if pd.isna(operator_str) or not operator_str:
        return None
    operator_str = str(operator_str).strip()
    return OPERATOR_MAPPING.get(operator_str, operator_str)

def load_and_process_csv1(csv_path: str) -> pd.DataFrame:
    """
    統計モデル検討.csv を読み込み、診断ルールデータに変換
    
    想定されるCSV構造:
    - ルールコード, ルール名, イベント, 角度, 演算子, 閾値, 重要度, 優先度
    """
    print(f"📖 CSV1を読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # カラム名の正規化（大文字小文字、空白を除去）
    df.columns = df.columns.str.strip().str.lower()
    
    print(f"   カラム: {list(df.columns)}")
    print(f"   行数: {len(df)}")
    
    # カラム名のマッピング（柔軟に対応）
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'ルール' in col_lower and 'コード' in col_lower:
            column_mapping[col] = 'rule_code'
        elif 'ルール' in col_lower and '名' in col_lower:
            column_mapping[col] = 'rule_name'
        elif 'イベント' in col_lower or 'event' in col_lower:
            column_mapping[col] = 'target_event'
        elif '角度' in col_lower or 'metric' in col_lower:
            column_mapping[col] = 'target_metric'
        elif '演算子' in col_lower or 'operator' in col_lower:
            column_mapping[col] = 'operator'
        elif '閾値' in col_lower or 'threshold' in col_lower or 'しきい' in col_lower:
            column_mapping[col] = 'threshold'
        elif '重要度' in col_lower or 'severity' in col_lower:
            column_mapping[col] = 'severity'
        elif '優先度' in col_lower or 'priority' in col_lower:
            column_mapping[col] = 'priority'
    
    # カラム名をリネーム
    df = df.rename(columns=column_mapping)
    
    # 必須カラムの確認
    required_cols = ['rule_code', 'target_metric', 'operator', 'threshold', 'severity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️  警告: 必須カラムが見つかりません: {missing_cols}")
        print(f"   利用可能なカラム: {list(df.columns)}")
    
    # データの正規化
    if 'target_metric' in df.columns:
        df['target_metric'] = df['target_metric'].apply(normalize_angle_name)
    if 'target_event' in df.columns:
        df['target_event'] = df['target_event'].apply(normalize_event_name)
    if 'operator' in df.columns:
        df['operator'] = df['operator'].apply(normalize_operator)
    
    return df

def load_and_process_csv2(csv_path: str) -> pd.DataFrame:
    """
    ランニング分類.csv を読み込み
    
    想定されるCSV構造:
    - 分類コード, 分類名, 説明など
    """
    print(f"📖 CSV2を読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip().str.lower()
    print(f"   カラム: {list(df.columns)}")
    print(f"   行数: {len(df)}")
    return df

def load_and_process_csv3(csv_path: str) -> pd.DataFrame:
    """
    コメント紐づけ.csv を読み込み、専門家アドバイスデータに変換
    
    想定されるCSV構造:
    - ルールコード, 課題名, 現象, 原因, 改善策, ドリル名, ドリルURL
    """
    print(f"📖 CSV3を読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip().str.lower()
    
    print(f"   カラム: {list(df.columns)}")
    print(f"   行数: {len(df)}")
    
    # カラム名のマッピング
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'ルール' in col_lower and 'コード' in col_lower:
            column_mapping[col] = 'rule_code'
        elif '課題' in col_lower and '名' in col_lower:
            column_mapping[col] = 'issue_name'
        elif '現象' in col_lower or 'observation' in col_lower:
            column_mapping[col] = 'observation'
        elif '原因' in col_lower or 'cause' in col_lower:
            column_mapping[col] = 'cause'
        elif '改善' in col_lower or 'action' in col_lower:
            column_mapping[col] = 'action'
        elif 'ドリル' in col_lower and '名' in col_lower:
            column_mapping[col] = 'drill_name'
        elif 'ドリル' in col_lower and ('url' in col_lower or 'リンク' in col_lower):
            column_mapping[col] = 'drill_url'
        elif '備考' in col_lower or 'notes' in col_lower:
            column_mapping[col] = 'additional_notes'
    
    df = df.rename(columns=column_mapping)
    
    return df

# ==========================================
# 5. データベースへの投入
# ==========================================

def insert_diagnosis_rules(conn, df: pd.DataFrame):
    """診断ルールをデータベースに投入"""
    cursor = conn.cursor()
    
    # 既存データを削除（オプション）
    cursor.execute("DELETE FROM diagnosis_rules;")
    
    inserted_count = 0
    for _, row in df.iterrows():
        try:
            # 必須フィールドの確認
            if pd.isna(row.get('rule_code')) or pd.isna(row.get('target_metric')):
                print(f"⚠️  スキップ: 必須フィールドが不足しています - {row.to_dict()}")
                continue
            
            cursor.execute("""
                INSERT INTO diagnosis_rules (
                    rule_code, rule_name, target_event, target_metric,
                    operator, threshold, severity, priority, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (rule_code) DO UPDATE SET
                    rule_name = EXCLUDED.rule_name,
                    target_event = EXCLUDED.target_event,
                    target_metric = EXCLUDED.target_metric,
                    operator = EXCLUDED.operator,
                    threshold = EXCLUDED.threshold,
                    severity = EXCLUDED.severity,
                    priority = EXCLUDED.priority,
                    updated_at = NOW();
            """, (
                str(row.get('rule_code', '')).strip(),
                str(row.get('rule_name', '')).strip() if not pd.isna(row.get('rule_name')) else '',
                normalize_event_name(row.get('target_event')) if not pd.isna(row.get('target_event')) else None,
                normalize_angle_name(row.get('target_metric', '')),
                normalize_operator(row.get('operator', 'lt')) if not pd.isna(row.get('operator')) else 'lt',
                float(row.get('threshold', 0)) if not pd.isna(row.get('threshold')) else 0.0,
                str(row.get('severity', 'medium')).strip().lower() if not pd.isna(row.get('severity')) else 'medium',
                int(row.get('priority', 0)) if not pd.isna(row.get('priority')) else 0,
                True
            ))
            inserted_count += 1
        except Exception as e:
            print(f"❌ エラー: 行の投入に失敗 - {e}")
            print(f"   データ: {row.to_dict()}")
            continue
    
    conn.commit()
    cursor.close()
    print(f"✅ 診断ルール {inserted_count} 件を投入しました")

def insert_expert_advice(conn, df: pd.DataFrame):
    """専門家アドバイスをデータベースに投入"""
    cursor = conn.cursor()
    
    # 既存データを削除（オプション）
    cursor.execute("DELETE FROM expert_advice;")
    
    inserted_count = 0
    for _, row in df.iterrows():
        try:
            if pd.isna(row.get('rule_code')):
                print(f"⚠️  スキップ: rule_codeが不足しています - {row.to_dict()}")
                continue
            
            cursor.execute("""
                INSERT INTO expert_advice (
                    rule_code, issue_name, observation, cause, action,
                    drill_name, drill_url, additional_notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                str(row.get('rule_code', '')).strip(),
                str(row.get('issue_name', '')).strip() if not pd.isna(row.get('issue_name')) else '',
                str(row.get('observation', '')).strip() if not pd.isna(row.get('observation')) else None,
                str(row.get('cause', '')).strip() if not pd.isna(row.get('cause')) else None,
                str(row.get('action', '')).strip() if not pd.isna(row.get('action')) else None,
                str(row.get('drill_name', '')).strip() if not pd.isna(row.get('drill_name')) else None,
                str(row.get('drill_url', '')).strip() if not pd.isna(row.get('drill_url')) else None,
                str(row.get('additional_notes', '')).strip() if not pd.isna(row.get('additional_notes')) else None,
            ))
            inserted_count += 1
        except Exception as e:
            print(f"❌ エラー: 行の投入に失敗 - {e}")
            print(f"   データ: {row.to_dict()}")
            continue
    
    conn.commit()
    cursor.close()
    print(f"✅ 専門家アドバイス {inserted_count} 件を投入しました")

# ==========================================
# 6. メイン処理
# ==========================================

def main():
    parser = argparse.ArgumentParser(description='CSVデータをPostgreSQLに移行')
    parser.add_argument('--csv-dir', type=str, required=True, help='CSVファイルが格納されているディレクトリ')
    parser.add_argument('--csv1', type=str, default='統計モデル検討.csv', help='診断ルールCSVファイル名')
    parser.add_argument('--csv2', type=str, default='ランニング分類.csv', help='ランニング分類CSVファイル名')
    parser.add_argument('--csv3', type=str, default='コメント紐づけ.csv', help='コメント紐づけCSVファイル名')
    parser.add_argument('--skip-csv2', action='store_true', help='CSV2をスキップ（未使用の場合）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 CSVデータ移行スクリプト開始")
    print("=" * 80)
    
    # データベース接続
    conn = get_db_connection()
    
    try:
        # テーブル作成
        create_tables(conn)
        
        # CSVファイルのパス
        csv1_path = os.path.join(args.csv_dir, args.csv1)
        csv2_path = os.path.join(args.csv_dir, args.csv2)
        csv3_path = os.path.join(args.csv_dir, args.csv3)
        
        # CSV1: 診断ルール
        if os.path.exists(csv1_path):
            df1 = load_and_process_csv1(csv1_path)
            insert_diagnosis_rules(conn, df1)
        else:
            print(f"⚠️  CSV1が見つかりません: {csv1_path}")
        
        # CSV2: ランニング分類（必要に応じて）
        if not args.skip_csv2 and os.path.exists(csv2_path):
            df2 = load_and_process_csv2(csv2_path)
            print(f"📊 CSV2データ: {len(df2)} 行（現在は使用しません）")
        
        # CSV3: 専門家アドバイス
        if os.path.exists(csv3_path):
            df3 = load_and_process_csv3(csv3_path)
            insert_expert_advice(conn, df3)
        else:
            print(f"⚠️  CSV3が見つかりません: {csv3_path}")
        
        print("=" * 80)
        print("✅ 移行完了!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

