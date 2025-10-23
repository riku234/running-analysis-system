#!/usr/bin/env python3
"""
統合アドバイス生成のテストスクリプト
Gemini APIを使わずにデータベースからアドバイスを生成してテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/services/advice_generation/app'))

# Gemini APIを使わないように環境変数を設定
os.environ['GEMINI_API_KEY'] = ''  # APIキーを空に設定

from main import generate_integrated_advice

async def test_advice_generation():
    """アドバイス生成をテスト"""
    print("=" * 80)
    print("🧪 統合アドバイス生成テスト（APIキーなし）")
    print("=" * 80)
    
    # テスト用の課題リスト（データベースに存在する課題）
    issues_list = ["体幹前傾", "左下腿角度大", "右下腿角度大"]
    
    print(f"\n📝 入力課題リスト: {issues_list}")
    print("⚠️  注意: Gemini APIキーが設定されていないため、データベースからアドバイスを生成します")
    print("処理実行中...\n")
    
    try:
        # 統合アドバイス生成（同期的に実行）
        result = await generate_integrated_advice(issues_list, None)
        
        print("\n" + "=" * 80)
        print("✅ 生成完了")
        print("=" * 80)
        print("\n📄 生成されたアドバイス:")
        print(result)
        
        # 確認
        print("\n" + "=" * 80)
        print("✅ 検証結果:")
        print("=" * 80)
        
        checks = {
            "【個別課題の詳細解説】": "【個別課題の詳細解説】" in result,
            "【総合的な改善のポイント】": "【総合的な改善のポイント】" in result,
            "【📊 現状のフォームについて】": "【📊 現状のフォームについて】" in result,
            "【🎯 改善のためのアクション】": "【🎯 改善のためのアクション】" in result,
            "1. 体幹前傾": "1. 体幹前傾" in result,
            "詳細:": "詳細:" in result,
            "推奨エクササイズ:": "推奨エクササイズ:" in result,
        }
        
        all_passed = True
        for check_name, is_found in checks.items():
            status = "✅" if is_found else "❌"
            print(f"{status} {check_name}: {'含まれている' if is_found else '含まれていない'}")
            if not is_found:
                all_passed = False
        
        # 長さ確認
        print(f"\n📊 アドバイスの長さ: {len(result)} 文字")
        
        # 各部分の詳細
        if "【個別課題の詳細解説】" in result:
            detail_start = result.find("【個別課題の詳細解説】")
            detail_end = result.find("【総合的な改善のポイント】")
            if detail_start >= 0 and detail_end > detail_start:
                detail_section = result[detail_start:detail_end]
                print(f"\n📋 【個別課題の詳細解説】セクション長: {len(detail_section)} 文字")
                print(f"   プレビュー: {detail_section[:200]}...")
        
        print(f"\n🎯 全体テスト結果: {'✅ 全て正常' if all_passed else '❌ 問題あり'}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_advice_generation())
