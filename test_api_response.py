#!/usr/bin/env python3
"""
実際のAPIレスポンスをテストするスクリプト
統合アドバイス生成APIを直接呼び出してレスポンスを確認
"""

import os
import json
import requests
from typing import List, Dict, Any

def test_integrated_advice_api():
    """統合アドバイス生成APIをテスト"""
    
    # APIエンドポイント（ローカル開発環境を想定）
    base_url = "http://localhost:8005"  # advice_generationサービス
    
    print("=" * 80)
    print("🧪 統合アドバイスAPIテスト")
    print("=" * 80)
    
    # テスト用の課題リスト
    issues_list = ["体幹前傾", "左下腿角度大"]
    
    # リクエストデータ
    request_data = {
        "video_id": "test-video-123",
        "issues_list": issues_list,
        "prompt_settings": None
    }
    
    print(f"📝 テスト課題: {issues_list}")
    print(f"🌐 APIエンドポイント: {base_url}/generate-integrated")
    print(f"📊 リクエストデータ: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    try:
        # API呼び出し
        response = requests.post(
            f"{base_url}/generate-integrated",
            json=request_data,
            timeout=30
        )
        
        print(f"\n📨 HTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API呼び出し成功!")
            
            print(f"\n📋 レスポンス構造:")
            print(f"   status: {result.get('status')}")
            print(f"   message: {result.get('message')}")
            print(f"   video_id: {result.get('video_id')}")
            
            integrated_advice = result.get('integrated_advice', '')
            print(f"   integrated_advice 長: {len(integrated_advice)} 文字")
            
            if integrated_advice:
                print(f"\n📄 生成されたアドバイス:")
                print("-" * 60)
                print(integrated_advice)
                print("-" * 60)
                
                # 詳細確認
                checks = {
                    "【個別課題の詳細解説】": "【個別課題の詳細解説】" in integrated_advice,
                    "【総合的な改善のポイント】": "【総合的な改善のポイント】" in integrated_advice,
                    "1. 体幹前傾": "1. 体幹前傾" in integrated_advice,
                    "2. 左下腿角度大": "2. 左下腿角度大" in integrated_advice,
                    "詳細:": "詳細:" in integrated_advice,
                    "推奨エクササイズ:": "推奨エクササイズ:" in integrated_advice,
                }
                
                print(f"\n✅ 内容検証結果:")
                all_passed = True
                for check_name, is_found in checks.items():
                    status = "✅" if is_found else "❌"
                    print(f"   {status} {check_name}: {'含まれている' if is_found else '含まれていない'}")
                    if not is_found:
                        all_passed = False
                
                print(f"\n🎯 全体結果: {'✅ 正常' if all_passed else '❌ 問題あり'}")
                
                # 個別課題の詳細解説セクションを抽出
                if "【個別課題の詳細解説】" in integrated_advice:
                    detail_start = integrated_advice.find("【個別課題の詳細解説】")
                    detail_end = integrated_advice.find("【総合的な改善のポイント】")
                    if detail_start >= 0 and detail_end > detail_start:
                        detail_section = integrated_advice[detail_start:detail_end]
                        print(f"\n📋 【個別課題の詳細解説】セクション ({len(detail_section)}文字):")
                        print(detail_section[:300] + "..." if len(detail_section) > 300 else detail_section)
            else:
                print("❌ integrated_advice が空です")
                
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            print(f"   レスポンス: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ APIサーバーに接続できません")
        print("   advice_generation サービスが起動していない可能性があります")
        print("   docker-compose up -d advice_generation を実行してください")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

def test_health_check():
    """ヘルスチェック"""
    base_url = "http://localhost:8005"
    
    print(f"\n🔍 ヘルスチェック: {base_url}")
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   HTTPステータス: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   サービス: {result.get('service')}")
            print(f"   バージョン: {result.get('version')}")
            print(f"   AIプロバイダー: {result.get('ai_provider')}")
        else:
            print(f"   レスポンス: {response.text}")
    except Exception as e:
        print(f"   ❌ 接続エラー: {e}")

if __name__ == "__main__":
    # まずヘルスチェック
    test_health_check()
    
    # 次に統合アドバイスAPIテスト
    test_integrated_advice_api()
