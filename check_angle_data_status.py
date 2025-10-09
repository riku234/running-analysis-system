#!/usr/bin/env python3
"""
各関節角度の時系列データ取得状況を確認するスクリプト
"""
import os
import sys

# プロジェクトルートのパスを追加
sys.path.append('/app')

import psycopg2

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📊 各関節角度の時系列データ取得状況確認")
    print("=" * 80)
    print()
    
    # 最新のrun_idを取得
    cursor.execute("SELECT id, video_id FROM runs ORDER BY created_at DESC LIMIT 1")
    latest_run = cursor.fetchone()
    
    if not latest_run:
        print("❌ データベースに走行記録がありません")
        sys.exit(1)
    
    run_id, video_id = latest_run
    print(f"🎯 最新の走行記録:")
    print(f"   Run ID: {run_id}")
    print(f"   Video ID: {video_id}")
    print()
    
    # 1. キーポイントデータの確認
    print("=" * 80)
    print("1️⃣ キーポイントデータ（時系列座標）")
    print("=" * 80)
    cursor.execute("""
        SELECT COUNT(DISTINCT frame_number) as frame_count,
               COUNT(*) as total_keypoints
        FROM keypoints
        WHERE run_id = %s
    """, (run_id,))
    kp_stats = cursor.fetchone()
    print(f"✅ フレーム数: {kp_stats[0]}")
    print(f"✅ 総キーポイント数: {kp_stats[1]}")
    if kp_stats[0] > 0:
        print(f"   （1フレームあたり約 {kp_stats[1] // kp_stats[0]} 個のランドマーク）")
    print()
    
    # サンプルデータを表示
    cursor.execute("""
        SELECT frame_number, landmark_name, x_coordinate, y_coordinate, visibility
        FROM keypoints
        WHERE run_id = %s AND frame_number = 0
        ORDER BY landmark_id
        LIMIT 5
    """, (run_id,))
    sample_kps = cursor.fetchall()
    print("   📋 フレーム0のサンプルデータ:")
    for kp in sample_kps:
        print(f"      {kp[1]}: x={kp[2]:.3f}, y={kp[3]:.3f}, vis={kp[4]:.3f}")
    print()
    
    # 2. 解析結果データの確認（角度関連）
    print("=" * 80)
    print("2️⃣ 解析結果データ（角度の統計値）")
    print("=" * 80)
    cursor.execute("""
        SELECT metric_name, value, unit, category
        FROM analysis_results
        WHERE run_id = %s AND (
            metric_name LIKE '%angle%' OR
            metric_name LIKE '%角度%' OR
            category = 'angle'
        )
        ORDER BY metric_name
    """, (run_id,))
    angle_results = cursor.fetchall()
    
    if angle_results:
        print(f"✅ 角度関連の解析結果: {len(angle_results)}件")
        for result in angle_results:
            print(f"   {result[0]}: {result[1]} {result[2] or ''} (category: {result[3] or 'N/A'})")
    else:
        print("❌ 角度関連の解析結果が保存されていません")
    print()
    
    # 3. 全解析結果の確認
    print("=" * 80)
    print("3️⃣ 全解析結果データ")
    print("=" * 80)
    cursor.execute("""
        SELECT COUNT(*), 
               COUNT(DISTINCT category) as category_count
        FROM analysis_results
        WHERE run_id = %s
    """, (run_id,))
    all_results = cursor.fetchone()
    print(f"✅ 総解析結果数: {all_results[0]}")
    print(f"✅ カテゴリ数: {all_results[1]}")
    print()
    
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM analysis_results
        WHERE run_id = %s
        GROUP BY category
        ORDER BY count DESC
    """, (run_id,))
    categories = cursor.fetchall()
    print("   📊 カテゴリ別内訳:")
    for cat in categories:
        print(f"      {cat[0] or 'NULL'}: {cat[1]}件")
    print()
    
    # 4. 結論
    print("=" * 80)
    print("📝 結論")
    print("=" * 80)
    print()
    print("✅ キーポイントの時系列データ:")
    print(f"   → {kp_stats[0]}フレーム分のキーポイント座標を保存済み")
    print(f"   → これらから各フレームの関節角度を計算可能")
    print()
    
    if angle_results:
        print("✅ 角度の統計値:")
        print(f"   → {len(angle_results)}種類の角度統計を保存済み")
        print("   → 平均値、最大値、最小値などの統計情報")
    else:
        print("⚠️  角度の統計値:")
        print("   → 角度の統計値は保存されていません")
    print()
    
    print("❓ 各フレームごとの角度時系列データ:")
    print("   → 現在は保存されていません")
    print("   → キーポイントから計算可能ですが、直接保存はしていません")
    print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
