#!/usr/bin/env python3
"""
データベーステーブル作成スクリプト
"""

import sys
sys.path.append('/app')

from db_utils import get_db_connection
import psycopg2

def create_tables():
    """
    全テーブルを作成する
    """
    
    # SQLファイルを読み込む
    with open('database_schema.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    conn = None
    cursor = None
    
    try:
        print("=" * 80)
        print("📊 データベーステーブル作成")
        print("=" * 80)
        print()
        
        # データベースに接続
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗しました")
            return False
        
        cursor = conn.cursor()
        
        print("📝 テーブルを作成しています...")
        print()
        
        # SQLを実行
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ テーブル作成完了!")
        print()
        
        # 作成されたテーブルを確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print("📋 作成されたテーブル:")
        for table in tables:
            print(f"   ✓ {table[0]}")
        
        print()
        print("=" * 80)
        print("✅ セットアップ完了!")
        print("=" * 80)
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)

