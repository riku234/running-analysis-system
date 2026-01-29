#!/usr/bin/env python3
"""
標準モデルキーポイントAPIの動作確認スクリプト
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def test_get_all_frames():
    """全フレーム取得のテスト"""
    print("=" * 60)
    print("テスト1: 全フレーム取得")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/standard_model/keypoints")
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ ステータス: {data.get('status')}")
        print(f"✅ 総フレーム数: {data.get('total_frames')}")
        
        if 'frames' in data:
            frame_keys = list(data['frames'].keys())
            print(f"✅ フレーム範囲: {min(frame_keys)} - {max(frame_keys)}")
            
            # フレーム0の詳細を確認
            if '0' in data['frames']:
                frame0 = data['frames']['0']
                keypoints_count = len(frame0.get('keypoints', []))
                print(f"✅ フレーム0のキーポイント数: {keypoints_count}")
                
                if keypoints_count > 0:
                    kp0 = frame0['keypoints'][0]
                    print(f"✅ キーポイント形式: {list(kp0.keys())}")
                    print(f"   例: {kp0}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: {e}")
        return False

def test_get_specific_frame(frame_num: int):
    """特定フレーム取得のテスト"""
    print("=" * 60)
    print(f"テスト2: 特定フレーム取得 (frame={frame_num})")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/standard_model/keypoints?frame={frame_num}")
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ ステータス: {data.get('status')}")
        print(f"✅ フレーム番号: {data.get('frame')}")
        
        keypoints = data.get('keypoints', [])
        print(f"✅ キーポイント数: {len(keypoints)}")
        
        if len(keypoints) > 0:
            # 主要キーポイントを確認
            landmarks = {
                "left_shoulder": 11,
                "right_shoulder": 12,
                "left_hip": 23,
                "right_hip": 24,
                "left_knee": 25,
                "right_knee": 26,
                "left_ankle": 27,
                "right_ankle": 28
            }
            
            print("\n主要キーポイント:")
            for name, idx in landmarks.items():
                if idx < len(keypoints):
                    kp = keypoints[idx]
                    print(f"  {name} (idx={idx}): x={kp['x']:.3f}, y={kp['y']:.3f}, visibility={kp['visibility']:.3f}")
            
            # 座標値の範囲チェック
            all_valid = True
            for i, kp in enumerate(keypoints):
                if not (0.0 <= kp['x'] <= 1.0 and 0.0 <= kp['y'] <= 1.0):
                    print(f"⚠️  キーポイント{i}: 座標値が範囲外 (x={kp['x']}, y={kp['y']})")
                    all_valid = False
            
            if all_valid:
                print("✅ すべてのキーポイントの座標値が0.0-1.0の範囲内")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: {e}")
        if hasattr(e.response, 'text'):
            print(f"   レスポンス: {e.response.text}")
        return False

def test_error_handling():
    """エラーハンドリングのテスト"""
    print("=" * 60)
    print("テスト3: エラーハンドリング (範囲外のフレーム番号)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/standard_model/keypoints?frame=101")
        
        if response.status_code == 400:
            print(f"✅ 期待通り400エラーが返されました")
            print(f"   エラーメッセージ: {response.json().get('detail', 'N/A')}")
            return True
        else:
            print(f"⚠️  予期しないステータスコード: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    print("標準モデルキーポイントAPIの動作確認を開始します...\n")
    
    results = []
    
    # テスト1: 全フレーム取得
    results.append(("全フレーム取得", test_get_all_frames()))
    print()
    
    # テスト2: 特定フレーム取得（フレーム0）
    results.append(("特定フレーム取得 (frame=0)", test_get_specific_frame(0)))
    print()
    
    # テスト3: 特定フレーム取得（フレーム50）
    results.append(("特定フレーム取得 (frame=50)", test_get_specific_frame(50)))
    print()
    
    # テスト4: エラーハンドリング
    results.append(("エラーハンドリング", test_error_handling()))
    print()
    
    # 結果サマリー
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    print()
    if all_passed:
        print("🎉 すべてのテストが成功しました！Phase 2はOKです。")
        return 0
    else:
        print("⚠️  一部のテストが失敗しました。確認してください。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
