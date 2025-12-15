"""
データベース内の診断ルールとアドバイスデータを確認するスクリプト

使用方法:
    python backend/scripts/check_db_data.py
"""

import sqlalchemy
from sqlalchemy import create_engine, text
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 環境変数の読み込み
load_dotenv()

def get_db_url():
    """環境変数からデータベースURLを構築"""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "app")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def check_data():
    """データベース内のデータを確認"""
    try:
        db_url = get_db_url()
        print(f"🔌 データベース接続: {db_url.replace(db_url.split('@')[0].split('//')[1].split(':')[0], '***')}")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # 1. ルールの数を確認
            try:
                rules_count = conn.execute(text("SELECT COUNT(*) FROM diagnosis_rules")).scalar()
                print(f"✅ ルール定義の数: {rules_count} 件")
            except Exception as e:
                print(f"❌ ルールテーブルの確認に失敗: {e}")
                print("   テーブルが存在しない可能性があります。database_schema.sqlを実行してください。")
                return
            
            # 2. アドバイスの数を確認
            try:
                advice_count = conn.execute(text("SELECT COUNT(*) FROM expert_advice")).scalar()
                print(f"✅ アドバイス文章の数: {advice_count} 件")
            except Exception as e:
                print(f"❌ アドバイステーブルの確認に失敗: {e}")
                print("   テーブルが存在しない可能性があります。database_schema.sqlを実行してください。")
                return
            
            # 3. アクティブなルールの数を確認
            try:
                active_rules_count = conn.execute(
                    text("SELECT COUNT(*) FROM diagnosis_rules WHERE is_active = TRUE")
                ).scalar()
                print(f"✅ アクティブなルール: {active_rules_count} 件")
            except Exception as e:
                print(f"⚠️  アクティブルールの確認に失敗: {e}")
            
            # 4. ルールとアドバイスの結合データを表示
            print("\n" + "=" * 80)
            print("📊 データのサンプル（最初の5件）")
            print("=" * 80)
            
            try:
                samples = conn.execute(text("""
                    SELECT 
                        r.rule_code,
                        r.rule_name,
                        r.target_event,
                        r.target_metric,
                        r.operator,
                        r.threshold,
                        r.severity,
                        r.priority,
                        r.is_active,
                        e.issue_name,
                        e.observation,
                        e.cause,
                        e.action,
                        e.drill_name,
                        e.drill_url
                    FROM diagnosis_rules r
                    LEFT JOIN expert_advice e ON r.rule_code = e.rule_code
                    ORDER BY r.priority DESC, r.rule_code ASC
                    LIMIT 5
                """)).fetchall()
                
                if samples:
                    for idx, sample in enumerate(samples, 1):
                        print(f"\n【サンプル {idx}】")
                        print(f"  ルールコード: {sample[0]}")
                        print(f"  ルール名: {sample[1]}")
                        print(f"  対象イベント: {sample[2] or '全イベント'}")
                        print(f"  対象角度: {sample[3]}")
                        print(f"  演算子: {sample[4]}")
                        print(f"  閾値: {sample[5]}")
                        print(f"  重要度: {sample[6]}")
                        print(f"  優先度: {sample[7]}")
                        print(f"  アクティブ: {'✅' if sample[8] else '❌'}")
                        
                        if sample[9]:  # issue_name
                            print(f"  課題名: {sample[9]}")
                            if sample[10]:  # observation
                                print(f"  現象: {sample[10][:100]}..." if len(sample[10]) > 100 else f"  現象: {sample[10]}")
                            if sample[11]:  # cause
                                print(f"  原因: {sample[11][:100]}..." if len(sample[11]) > 100 else f"  原因: {sample[11]}")
                            if sample[12]:  # action
                                print(f"  改善策: {sample[12][:100]}..." if len(sample[12]) > 100 else f"  改善策: {sample[12]}")
                            if sample[13]:  # drill_name
                                print(f"  ドリル: {sample[13]}")
                            if sample[14]:  # drill_url
                                print(f"  ドリルURL: {sample[14]}")
                        else:
                            print("  ⚠️  アドバイスデータが紐づいていません")
                else:
                    print("⚠️  データが見つかりません。移行スクリプトを実行しましたか？")
                    print("\n💡 次のコマンドでCSVデータを移行してください:")
                    print("   python backend/scripts/migrate_csv_to_db.py --csv-dir /path/to/csv/files")
            
            except Exception as e:
                print(f"❌ サンプルデータの取得に失敗: {e}")
                import traceback
                traceback.print_exc()
            
            # 5. ルールとアドバイスの紐づき状況を確認
            print("\n" + "=" * 80)
            print("📈 ルールとアドバイスの紐づき状況")
            print("=" * 80)
            
            try:
                join_status = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_rules,
                        COUNT(e.id) as rules_with_advice,
                        COUNT(*) - COUNT(e.id) as rules_without_advice
                    FROM diagnosis_rules r
                    LEFT JOIN expert_advice e ON r.rule_code = e.rule_code
                    WHERE r.is_active = TRUE
                """)).fetchone()
                
                if join_status:
                    print(f"  総ルール数: {join_status[0]} 件")
                    print(f"  アドバイス有り: {join_status[1]} 件")
                    print(f"  アドバイス無し: {join_status[2]} 件")
                    
                    if join_status[2] > 0:
                        print(f"\n  ⚠️  {join_status[2]} 件のルールにアドバイスが紐づいていません")
                        print("     コメント紐づけ.csvを確認してください")
            
            except Exception as e:
                print(f"⚠️  紐づき状況の確認に失敗: {e}")
            
            # 6. イベント種別ごとのルール数を確認
            print("\n" + "=" * 80)
            print("📊 イベント種別ごとのルール数")
            print("=" * 80)
            
            try:
                event_counts = conn.execute(text("""
                    SELECT 
                        COALESCE(target_event, '全イベント') as event_type,
                        COUNT(*) as count
                    FROM diagnosis_rules
                    WHERE is_active = TRUE
                    GROUP BY target_event
                    ORDER BY count DESC
                """)).fetchall()
                
                for event_type, count in event_counts:
                    print(f"  {event_type}: {count} 件")
            
            except Exception as e:
                print(f"⚠️  イベント種別の集計に失敗: {e}")
            
            # 7. 角度種別ごとのルール数を確認
            print("\n" + "=" * 80)
            print("📊 角度種別ごとのルール数")
            print("=" * 80)
            
            try:
                metric_counts = conn.execute(text("""
                    SELECT 
                        target_metric,
                        COUNT(*) as count
                    FROM diagnosis_rules
                    WHERE is_active = TRUE
                    GROUP BY target_metric
                    ORDER BY count DESC
                """)).fetchall()
                
                for metric, count in metric_counts:
                    print(f"  {metric}: {count} 件")
            
            except Exception as e:
                print(f"⚠️  角度種別の集計に失敗: {e}")
            
            print("\n" + "=" * 80)
            print("✅ データ確認完了")
            print("=" * 80)
    
    except sqlalchemy.exc.OperationalError as e:
        print(f"❌ データベース接続エラー: {e}")
        print("\n💡 確認事項:")
        print("   1. データベースが起動しているか")
        print("   2. .envファイルの接続情報が正しいか")
        print("   3. ポート5432が公開されているか（Dockerの場合）")
        print(f"\n   現在の接続情報:")
        print(f"   DB_HOST: {os.getenv('DB_HOST', '未設定')}")
        print(f"   DB_PORT: {os.getenv('DB_PORT', '未設定')}")
        print(f"   DB_NAME: {os.getenv('DB_NAME', '未設定')}")
        print(f"   DB_USER: {os.getenv('DB_USER', '未設定')}")
    
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("🔍 データベースデータ確認スクリプト")
    print("=" * 80)
    print()
    check_data()



