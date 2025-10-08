#!/usr/bin/env python3
"""
データベースの中身を確認するスクリプト
"""
import sys
sys.path.append('backend/services/video_processing')
from db_utils import get_db_connection

def check_database():
    conn = get_db_connection()
    if not conn:
        print("❌ データベース接続に失敗しました")
        return
    
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*60)
        print("📊 データベース概要")
        print("="*60)
        
        # 各テーブルの件数
        tables = ['users', 'runs', 'keypoints', 'analysis_results', 'events', 'advice']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20s}: {count:8,d} 件")
        
        # 最新の走行記録
        print("\n" + "="*60)
        print("🏃 最新の走行記録（runs）")
        print("="*60)
        cursor.execute("""
            SELECT id, video_id, original_filename, analysis_status, 
                   total_frames, created_at
            FROM runs
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        print(f"{'ID':<5} {'Video ID':<38} {'ファイル名':<20} {'ステータス':<12} {'フレーム':<8} {'作成日時'}")
        print("-" * 120)
        for row in cursor.fetchall():
            print(f"{row[0]:<5} {row[1]:<38} {row[2]:<20} {row[3]:<12} {row[4] or 0:<8} {row[5]}")
        
        # 最新の解析結果サンプル
        print("\n" + "="*60)
        print("📈 最新の解析結果サンプル（analysis_results）")
        print("="*60)
        cursor.execute("""
            SELECT run_id, metric_name, value
            FROM analysis_results
            ORDER BY id DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"Run {row[0]}: {row[1]:<45s} = {row[2]:.4f}")
        
        # イベントサマリー
        print("\n" + "="*60)
        print("👣 イベントサマリー（events）")
        print("="*60)
        cursor.execute("""
            SELECT run_id, event_type, COUNT(*) as count
            FROM events
            GROUP BY run_id, event_type
            ORDER BY run_id DESC
            LIMIT 20
        """)
        
        current_run = None
        for row in cursor.fetchall():
            if current_run != row[0]:
                current_run = row[0]
                print(f"\nRun {row[0]}:")
            print(f"  {row[1]:<20s}: {row[2]:3d} 回")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database()
