#!/usr/bin/env python3
"""
ユーザー登録スクリプト
Running Analysis System用のユーザーをデータベースに登録します
"""

import psycopg2
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 登録するユーザーリスト
USERS = [
    ("vf_yaji", "VF矢治"),
    ("vf_ono", "VF大野"),
    ("vf_hirokawa", "VF広川"),
    ("x_ae", "X阿江"),
    ("x_masuda", "X増田"),
    ("x_komatsu", "X小松"),
    ("x_suzuki", "X鈴木"),
    ("x_konno", "X近野"),
    ("guest1", "ゲスト1"),
    ("guest2", "ゲスト2"),
    ("guest3", "ゲスト3"),
    ("guest4", "ゲスト4"),
    ("guest5", "ゲスト5"),
    ("default_user", "デフォルトユーザー"),  # 既存データ用
]

def setup_users():
    """ユーザーをデータベースに登録"""
    try:
        # データベースに接続
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        
        print("=" * 60)
        print("ユーザー登録スクリプト開始")
        print("=" * 60)
        print()
        
        # 既存ユーザーを確認
        cursor.execute("SELECT user_id, username FROM users ORDER BY user_id")
        existing_users = cursor.fetchall()
        
        if existing_users:
            print(f"📊 既存ユーザー: {len(existing_users)}名")
            for user_id, username in existing_users:
                print(f"   - {user_id}: {username}")
            print()
        else:
            print("📊 既存ユーザー: なし")
            print()
        
        # 各ユーザーを登録（既に存在する場合は更新）
        registered_count = 0
        updated_count = 0
        
        for user_id, username in USERS:
            try:
                # INSERT ON CONFLICT で既存の場合は更新
                cursor.execute("""
                    INSERT INTO users (user_id, username, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        updated_at = NOW()
                    RETURNING (xmax = 0) AS inserted
                """, (user_id, username))
                
                result = cursor.fetchone()
                is_new = result[0] if result else False
                
                if is_new:
                    print(f"✅ 新規登録: {user_id} ({username})")
                    registered_count += 1
                else:
                    print(f"🔄 更新: {user_id} ({username})")
                    updated_count += 1
                    
            except Exception as e:
                print(f"❌ エラー ({user_id}): {e}")
        
        # コミット
        conn.commit()
        
        print()
        print("=" * 60)
        print("📊 登録結果")
        print("=" * 60)
        print(f"✅ 新規登録: {registered_count}名")
        print(f"🔄 更新: {updated_count}名")
        print(f"📝 合計: {len(USERS)}名")
        print()
        
        # 最終確認
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"💾 データベース内の総ユーザー数: {total_users}名")
        print()
        
        # 全ユーザーを表示
        cursor.execute("SELECT user_id, username FROM users ORDER BY user_id")
        all_users = cursor.fetchall()
        
        print("📋 登録済みユーザー一覧:")
        for user_id, username in all_users:
            print(f"   {user_id:20s} → {username}")
        
        print()
        print("=" * 60)
        print("✅ ユーザー登録完了")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = setup_users()
    exit(0 if success else 1)
