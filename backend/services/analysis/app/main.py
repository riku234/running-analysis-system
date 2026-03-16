import math
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional, Tuple

app = FastAPI(
    title="Z-Score Analysis Service",
    description="イベント別Z値によるランニングフォーム分析サービス",
    version="3.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# イベント別標準モデルデータの定義 (Z値分析用)
# =============================================================================
def get_event_based_standard_model():
    """
    4つの主要イベントにおける各指標の平均値と標準偏差を返す
    
    Returns:
        Dict: イベント別の標準モデルデータ
    """
    standard_model = {
        'right_strike': {
            '体幹角度': {'mean': 3.9639, 'std': 3.3558},
            '右大腿角度': {'mean': -14.5972, 'std': 12.6164},
            '右下腿角度': {'mean': 3.3022, 'std': 24.2673},
            '左大腿角度': {'mean': -1.0871, 'std': 13.0495},
            '左下腿角度': {'mean': 64.6344, 'std': 24.7028}
        },
        'right_off': {
            '体幹角度': {'mean': 5.2522, 'std': 2.7204},
            '右大腿角度': {'mean': 9.3522, 'std': 16.0312},
            '右下腿角度': {'mean': 37.7302, 'std': 14.3688},
            '左大腿角度': {'mean': -30.5691, 'std': 16.4680},
            '左下腿角度': {'mean': 28.3607, 'std': 6.9376}
        },
        'left_strike': {
            '体幹角度': {'mean': 3.7095, 'std': 3.3154},
            '右大腿角度': {'mean': 1.2450, 'std': 11.5915},
            '右下腿角度': {'mean': 63.5634, 'std': 25.0095},
            '左大腿角度': {'mean': -15.0547, 'std': 12.7922},
            '左下腿角度': {'mean': 2.8682, 'std': 24.8263}
        },
        'left_off': {
            '体幹角度': {'mean': 4.3644, 'std': 3.1738},
            '右大腿角度': {'mean': -28.5075, 'std': 16.6879},
            '右下腿角度': {'mean': 29.9012, 'std': 6.8009},
            '左大腿角度': {'mean': 8.5351, 'std': 15.2813},
            '左下腿角度': {'mean': 37.1213, 'std': 12.3492}
        }
    }
    return standard_model

# =============================================================================
# 足接地・離地検出機能
# =============================================================================
def detect_foot_strikes_advanced(keypoints_data: List[Dict], video_fps: float) -> List[Tuple[int, str, str]]:
    """
    高度な足接地・離地検出機能（改良版）
    
    Args:
        keypoints_data: 全フレームのキーポイントデータ
        video_fps: 動画のフレームレート
    
    Returns:
        List[Tuple[int, str, str]]: (フレーム番号, 足, イベント種類)のリスト
    """
    all_events = []
    try:
        print("🦶 足接地・離地検出を開始します...")
        
        # 足首と腰のY座標を取得
        left_ankle_y = []
        right_ankle_y = []
        hip_y = []  # 腰のY座標（左右の平均）
        
        for frame_data in keypoints_data:
            if 'keypoints' in frame_data:
                keypoints = frame_data['keypoints']
                # MediaPipeのインデックス（左腰: 23, 右腰: 24, 左足首: 27, 右足首: 28）
                left_hip_y = keypoints[23]['y'] if len(keypoints) > 23 else 0
                right_hip_y = keypoints[24]['y'] if len(keypoints) > 24 else 0
                hip_center_y = (left_hip_y + right_hip_y) / 2 if (left_hip_y > 0 and right_hip_y > 0) else 0
                
                left_ankle_y.append(keypoints[27]['y'] if len(keypoints) > 27 else 0)
                right_ankle_y.append(keypoints[28]['y'] if len(keypoints) > 28 else 0)
                hip_y.append(hip_center_y)
        
        print(f"   📊 データフレーム数: {len(keypoints_data)}")
        
        # 接地・離地を統合検出（ゼロクロス法を使用）
        left_events = detect_strikes_and_offs_zero_crossing(left_ankle_y, hip_y, video_fps, 'left')
        right_events = detect_strikes_and_offs_zero_crossing(right_ankle_y, hip_y, video_fps, 'right')
        
        # イベントを種類別に分類
        left_strikes = [frame for frame, event_type in left_events if event_type == 'strike']
        left_offs = [frame for frame, event_type in left_events if event_type == 'off']
        right_strikes = [frame for frame, event_type in right_events if event_type == 'strike']
        right_offs = [frame for frame, event_type in right_events if event_type == 'off']
        
        print(f"   ✅ 検出完了 - 左足: 接地{len(left_strikes)}回, 離地{len(left_offs)}回")
        print(f"   ✅ 検出完了 - 右足: 接地{len(right_strikes)}回, 離地{len(right_offs)}回")
        
        # 全イベントをリストに統合
        all_events = []
        for frame in left_strikes:
            all_events.append((frame, 'left', 'strike'))
        for frame in left_offs:
            all_events.append((frame, 'left', 'off'))
        for frame in right_strikes:
            all_events.append((frame, 'right', 'strike'))
        for frame in right_offs:
            all_events.append((frame, 'right', 'off'))
        
        # フレーム順にソート
        all_events.sort(key=lambda x: x[0])
        
        print(f"   📊 統合イベント数: {len(all_events)}")
        if all_events:
            print(f"   📝 最初の5イベント: {all_events[:5]}")
        
        return all_events
        
    except Exception as e:
        print(f"❌ 足接地検出エラー: {e}")
        import traceback
        traceback.print_exc()
        # エラー時も統一されたリスト形式で返却
        return []

def detect_strikes_and_offs_zero_crossing(ankle_y_coords: List[float], hip_y_coords: List[float], video_fps: float, foot_side: str) -> List[Tuple[int, str]]:
    """
    ゼロクロス法による着地・離地検出（改良版）
    
    足首が腰に対する相対的な高さの平均値を下回った瞬間（＝着地に向かう動き）を検知する
    ノイズに対してより堅牢な検出方法
    
    Args:
        ankle_y_coords: 足首のY座標リスト
        hip_y_coords: 腰のY座標リスト（左右の平均）
        video_fps: 動画のフレームレート
        foot_side: 'left' または 'right'
    
    Returns:
        List[Tuple[int, str]]: (フレーム番号, イベント種類) のリスト
    """
    if not ankle_y_coords or len(ankle_y_coords) < 10:
        return []
    
    if len(hip_y_coords) != len(ankle_y_coords):
        print(f"   ⚠️  {foot_side}足 腰と足首のデータ数が一致しません（腰:{len(hip_y_coords)}, 足首:{len(ankle_y_coords)}）")
        # フォールバック: 従来の方法を使用
        return detect_strikes_and_offs_from_y_coords(ankle_y_coords, video_fps, foot_side)
    
    ankle_array = np.array(ankle_y_coords)
    hip_array = np.array(hip_y_coords)
    
    print(f"   📊 {foot_side}足 足首Y座標範囲: {np.min(ankle_array):.3f} - {np.max(ankle_array):.3f}")
    print(f"   📊 {foot_side}足 腰Y座標範囲: {np.min(hip_array):.3f} - {np.max(hip_array):.3f}")
    
    # ===== 有効データのみを抽出 =====
    valid_threshold = 0.1  # Y座標が0.1以上を有効とみなす
    valid_mask = (ankle_array > valid_threshold) & (hip_array > valid_threshold)
    valid_indices = np.where(valid_mask)[0]
    
    if len(valid_indices) < 10:
        print(f"   ❌ {foot_side}足 有効データ不足: {len(valid_indices)}個")
        return []
    
    valid_ankle_y = ankle_array[valid_indices]
    valid_hip_y = hip_array[valid_indices]
    
    excluded_count = len(ankle_array) - len(valid_ankle_y)
    if excluded_count > 0:
        print(f"   🔍 {foot_side}足 データ除外: {excluded_count}個の無効フレームを除外")
        print(f"   ✅ {foot_side}足 有効データ: {len(valid_ankle_y)}個（約{len(valid_ankle_y)/video_fps:.1f}秒）")
    
    # ===== ゼロクロス法の実装 =====
    # 1. 腰に対する相対的な高さを計算
    relative_height = valid_ankle_y - valid_hip_y
    
    # 2. 相対的な高さの平均値を計算（ゼロクロスの基準）
    mean_relative_height = np.mean(relative_height)
    
    print(f"   📊 {foot_side}足 相対的高さの平均値: {mean_relative_height:.4f}")
    print(f"   📊 {foot_side}足 相対的高さの範囲: {np.min(relative_height):.4f} - {np.max(relative_height):.4f}")
    
    # 3. 平滑化（ノイズを軽減）
    try:
        from scipy import ndimage
        sigma = max(1.0, video_fps * 0.03)  # 0.03秒相当
        smoothed_relative_height = ndimage.gaussian_filter1d(relative_height, sigma=sigma)
    except ImportError:
        # scipyがない場合は移動平均
        window_size = max(3, int(video_fps * 0.1))
        if len(relative_height) < window_size:
            return []
        smoothed_relative_height = np.convolve(relative_height, np.ones(window_size)/window_size, mode='same')
    
    # 4. ゼロクロス検出（平均値を下回る瞬間 = 着地）
    strikes = []
    for i in range(1, len(smoothed_relative_height)):
        # 平均値を上回っていた状態から、平均値を下回った瞬間
        if smoothed_relative_height[i-1] > mean_relative_height and smoothed_relative_height[i] <= mean_relative_height:
            strikes.append(i)
    
    # 5. ゼロクロス検出（平均値を上回る瞬間 = 離地）
    offs = []
    for i in range(1, len(smoothed_relative_height)):
        # 平均値を下回っていた状態から、平均値を上回った瞬間
        if smoothed_relative_height[i-1] < mean_relative_height and smoothed_relative_height[i] >= mean_relative_height:
            offs.append(i)
    
    # 6. 最小間隔のフィルタリング（短すぎる間隔のイベントを除外）
    min_distance = max(3, int(video_fps * 0.15))  # 最小間隔0.15秒
    
    filtered_strikes = []
    last_strike = -min_distance
    for strike_idx in strikes:
        if strike_idx - last_strike >= min_distance:
            filtered_strikes.append(strike_idx)
            last_strike = strike_idx
    
    filtered_offs = []
    last_off = -min_distance
    for off_idx in offs:
        if off_idx - last_off >= min_distance:
            filtered_offs.append(off_idx)
            last_off = off_idx
    
    print(f"   🦶 {foot_side}足 ゼロクロス法検出: 接地{len(filtered_strikes)}回, 離地{len(filtered_offs)}回")
    
    # 7. イベントリストを作成（元のフレーム番号に変換）
    events = []
    
    for strike_idx in filtered_strikes:
        original_frame = valid_indices[strike_idx]
        events.append((int(original_frame), 'strike'))
        print(f"   🦶 {foot_side}足接地: フレーム{original_frame}, 相対高さ={smoothed_relative_height[strike_idx]:.4f}")
    
    for off_idx in filtered_offs:
        original_frame = valid_indices[off_idx]
        events.append((int(original_frame), 'off'))
        print(f"   🚁 {foot_side}足離地: フレーム{original_frame}, 相対高さ={smoothed_relative_height[off_idx]:.4f}")
    
    # 8. フレーム番号でソート
    events.sort(key=lambda x: x[0])
    
    # 9. 論理的な順序チェック
    events = validate_event_sequence(events, foot_side)
    
    return events

def detect_strikes_and_offs_from_y_coords(y_coords: List[float], video_fps: float, foot_side: str) -> List[Tuple[int, str]]:
    """
    Y座標から接地（極小値）と離地（極大値）を統合検出（従来の方法、フォールバック用）
    Y=0などの異常値を自動的に除外して処理
    
    Args:
        y_coords: 足首のY座標リスト
        video_fps: 動画のフレームレート
        foot_side: 'left' または 'right'
    
    Returns:
        List[Tuple[int, str]]: (フレーム番号, イベント種類) のリスト
    """
    if not y_coords or len(y_coords) < 10:
        return []
    
    y_array = np.array(y_coords)
    print(f"   📊 {foot_side}足 Y座標範囲（全体）: {np.min(y_array):.3f} - {np.max(y_array):.3f}")
    
    # ===== 新機能：有効データのみを抽出 =====
    # Y=0などの異常値を除外（ランナー画面外のフレームを除外）
    valid_threshold = 0.1  # Y座標が0.1以上を有効とみなす
    valid_indices = np.where(y_array > valid_threshold)[0]
    valid_y = y_array[valid_indices]
    
    if len(valid_y) < 10:
        print(f"   ❌ 有効データ不足: {len(valid_y)}個 / {len(y_array)}個")
        print(f"   💡 ランナーが画面内にいる時間が短すぎます（最低10フレーム必要）")
        return []
    
    excluded_count = len(y_array) - len(valid_y)
    if excluded_count > 0:
        print(f"   🔍 データ除外: {excluded_count}個のY≤{valid_threshold}フレームを除外")
        print(f"   ✅ 有効データ: {len(valid_y)}個（約{len(valid_y)/video_fps:.1f}秒）")
        print(f"   📊 有効Y座標範囲: {np.min(valid_y):.3f} - {np.max(valid_y):.3f}")
        print(f"   📊 有効範囲: Frame {valid_indices[0]} - {valid_indices[-1]}")
    
    # 有効データが短すぎる場合は警告
    if len(valid_y) < 30:  # 1秒未満
        print(f"   ⚠️  有効データが短い: {len(valid_y)/video_fps:.1f}秒（推奨: 3秒以上）")
    # ===== ここまで新機能 =====
    
    # 1. ガウシアンフィルタによる平滑化（有効データのみ）
    try:
        from scipy import ndimage
        sigma = max(1.0, video_fps * 0.03)  # 0.03秒相当
        smoothed_y = ndimage.gaussian_filter1d(valid_y, sigma=sigma)
    except ImportError:
        # scipyがない場合は移動平均
        window_size = max(3, int(video_fps * 0.1))
        if len(valid_y) < window_size:
            return []
        smoothed_y = np.convolve(valid_y, np.ones(window_size)/window_size, mode='same')
    
    print(f"   🔧 {foot_side}足 平滑化後Y座標範囲: {np.min(smoothed_y):.3f} - {np.max(smoothed_y):.3f}")
    
    # 2. scipy.signal.find_peaksを使用した極値検出（有効データのみ）
    try:
        from scipy.signal import find_peaks
        
        # 接地検出（極小値 = 足首が最も下）
        # Y座標を反転して極大値として検出
        inverted_y = -smoothed_y
        min_distance = max(3, int(video_fps * 0.15))  # 最小間隔0.15秒（より短く）
        height_threshold = np.percentile(inverted_y, 50)  # 上位50%の極値（より寛容）
        
        print(f"   🔍 height_threshold（接地）: {height_threshold:.4f}")
        
        strike_peaks, strike_properties = find_peaks(
            inverted_y,
            distance=min_distance,
            height=height_threshold,
            prominence=0.002  # 突出度をより小さく（より寛容）
        )
        
        # 離地検出（極大値 = 足首が最も上）
        off_peaks, off_properties = find_peaks(
            smoothed_y,
            distance=min_distance,
            height=np.percentile(smoothed_y, 50),  # 上位50%の極値（より寛容）
            prominence=0.002  # 突出度をより小さく（より寛容）
        )
        
        print(f"   🦶 {foot_side}足 find_peaks検出: 接地{len(strike_peaks)}回, 離地{len(off_peaks)}回")
        
    except ImportError:
        print(f"   ⚠️  scipy.signal未利用 - 従来方式で検出します")
        # scipyがない場合は従来の方式でフォールバック
        strike_peaks = []
        off_peaks = []
    
    # 3. イベントリストを作成・ソート
    # ===== 修正：検出されたインデックスを元のフレーム番号に変換 =====
    events = []
    
    # 接地イベントを追加
    for peak_idx in strike_peaks:
        original_frame = valid_indices[peak_idx]  # 元のフレーム番号に戻す
        events.append((int(original_frame), 'strike'))
        print(f"   🦶 {foot_side}足接地: フレーム{original_frame}, Y={y_array[original_frame]:.3f}")
    
    # 離地イベントを追加
    for peak_idx in off_peaks:
        original_frame = valid_indices[peak_idx]  # 元のフレーム番号に戻す
        events.append((int(original_frame), 'off'))
        print(f"   🚁 {foot_side}足離地: フレーム{original_frame}, Y={y_array[original_frame]:.3f}")
    # ===== ここまで修正 =====
    
    # 4. フレーム番号でソート
    events.sort(key=lambda x: x[0])
    
    # 5. 論理的な順序チェック（接地→離地→接地...）
    events = validate_event_sequence(events, foot_side)
    
    return events

def validate_event_sequence(events: List[Tuple[int, str]], foot_side: str) -> List[Tuple[int, str]]:
    """
    イベントの論理的順序をチェック・修正
    
    Args:
        events: (フレーム番号, イベント種類) のリスト
        foot_side: 'left' または 'right'
    
    Returns:
        List[Tuple[int, str]]: 修正されたイベントリスト
    """
    if not events:
        return []
    
    validated_events = []
    last_event_type = None
    
    for frame, event_type in events:
        # 同じイベントが連続する場合はスキップ
        if event_type == last_event_type:
            print(f"   ⚠️  {foot_side}足 重複イベントをスキップ: フレーム{frame} {event_type}")
            continue
        
        validated_events.append((frame, event_type))
        last_event_type = event_type
    
    print(f"   ✅ {foot_side}足 検証後イベント数: {len(validated_events)}")
    return validated_events

def get_all_events_sorted(events_dict: Dict[str, List[int]]) -> List[Tuple[int, str, str]]:
    """
    全イベントをフレーム番号順にソートして出力形式に変換
    
    Args:
        events_dict: detect_foot_strikes_advancedの出力
    
    Returns:
        List[Tuple[int, str, str]]: (フレーム番号, 足, イベント種類) のリスト
    """
    all_events = []
    
    # 各イベントタイプを追加
    for frame in events_dict.get('left_strikes', []):
        all_events.append((frame, 'left', 'strike'))
    
    for frame in events_dict.get('left_offs', []):
        all_events.append((frame, 'left', 'off'))
    
    for frame in events_dict.get('right_strikes', []):
        all_events.append((frame, 'right', 'strike'))
    
    for frame in events_dict.get('right_offs', []):
        all_events.append((frame, 'right', 'off'))
    
    # フレーム番号でソート
    all_events.sort(key=lambda x: x[0])
    
    return all_events

def convert_events_list_to_dict(all_events: List[Tuple[int, str, str]]) -> Dict[str, List[int]]:
    """
    all_eventsリストを辞書形式に変換する
    
    Args:
        all_events: [(frame, side, event_type), ...] 形式のリスト
    
    Returns:
        Dict: {'left_strikes': [...], 'left_offs': [...], ...} 形式の辞書
    """
    events_dict = {
        'left_strikes': [],
        'left_offs': [],
        'right_strikes': [],
        'right_offs': []
    }
    
    for frame, side, event_type in all_events:
        key = f"{side}_{event_type}s"
        if key in events_dict:
            events_dict[key].append(frame)
    
    # フレーム番号でソート
    for key in events_dict:
        events_dict[key].sort()
    
    return events_dict

# =============================================================================
# ワンサイクル特定・解析機能
# =============================================================================
def identify_best_running_cycle(events: Dict[str, List[int]], keypoints_data: List[Dict], video_fps: float) -> Optional[Dict[str, Any]]:
    """
    動画から最も明確なワンサイクルを特定
    
    Args:
        events: 検出された全イベント
        keypoints_data: キーポイントデータ
        video_fps: フレームレート
    
    Returns:
        Dict: 最良サイクルの情報、またはNone
    """
    try:
        print("🔍 ワンサイクル特定を開始します...")
        
        # 1. サイクル候補を抽出
        cycle_candidates = extract_cycle_candidates(events, video_fps)
        
        if not cycle_candidates:
            print("   ⚠️  サイクル候補が見つかりませんでした")
            return None
        
        print(f"   📊 サイクル候補数: {len(cycle_candidates)}")
        
        # 2. 各サイクルの品質を評価
        scored_cycles = []
        for i, cycle in enumerate(cycle_candidates):
            quality_score = evaluate_cycle_quality(cycle, keypoints_data, video_fps)
            scored_cycles.append((cycle, quality_score))
            print(f"   📈 サイクル{i+1}: スコア{quality_score:.2f}")
        
        # 3. 最高スコアのサイクルを選択
        best_cycle, best_score = max(scored_cycles, key=lambda x: x[1])
        
        print(f"   ✅ 最良サイクル選択: スコア{best_score:.2f}")
        print(f"      期間: フレーム{best_cycle['start_frame']}-{best_cycle['end_frame']}")
        print(f"      時間: {best_cycle['start_frame']/video_fps:.2f}-{best_cycle['end_frame']/video_fps:.2f}秒")
        
        return best_cycle
        
    except Exception as e:
        print(f"❌ サイクル特定エラー: {e}")
        return None

def extract_cycle_candidates(events: Dict[str, List[int]], video_fps: float) -> List[Dict[str, Any]]:
    """
    完全なサイクル候補を抽出
    
    サイクル定義: 右足接地 → 右足離地 → 左足接地 → 左足離地 → 次の右足接地
    
    Args:
        events: 検出されたイベント
        video_fps: フレームレート
    
    Returns:
        List[Dict]: サイクル候補のリスト
    """
    candidates = []
    
    right_strikes = events.get('right_strikes', [])
    right_offs = events.get('right_offs', [])
    left_strikes = events.get('left_strikes', [])
    left_offs = events.get('left_offs', [])
    
    if len(right_strikes) < 2:
        return candidates
    
    # 連続する右足接地をサイクルの境界として使用
    for i in range(len(right_strikes) - 1):
        cycle_start = right_strikes[i]
        cycle_end = right_strikes[i + 1]
        
        # サイクル内のイベントを収集
        cycle_events = {
            'right_strike': cycle_start,
            'right_off': None,
            'left_strike': None,
            'left_off': None
        }
        
        # 右足離地を探す
        for off_frame in right_offs:
            if cycle_start < off_frame < cycle_end:
                cycle_events['right_off'] = off_frame
                break
        
        # 左足接地を探す
        for strike_frame in left_strikes:
            if cycle_start < strike_frame < cycle_end:
                cycle_events['left_strike'] = strike_frame
                break
        
        # 左足離地を探す
        for off_frame in left_offs:
            if cycle_start < off_frame < cycle_end:
                cycle_events['left_off'] = off_frame
                break
        
        # 完全なサイクルかチェック
        if all(event is not None for event in cycle_events.values()):
            cycle_duration = (cycle_end - cycle_start) / video_fps
            
            # 妥当な時間範囲（0.2-3.0秒）より寛容に
            if 0.2 <= cycle_duration <= 3.0:
                candidates.append({
                    'start_frame': cycle_start,
                    'end_frame': cycle_end,
                    'duration': cycle_duration,
                    'events': cycle_events
                })
    
    return candidates

def evaluate_cycle_quality(cycle: Dict[str, Any], keypoints_data: List[Dict], video_fps: float) -> float:
    """
    サイクルの品質を評価
    
    Args:
        cycle: サイクル情報
        keypoints_data: キーポイントデータ
        video_fps: フレームレート
    
    Returns:
        float: 品質スコア（0-100）
    """
    score = 0.0
    
    try:
        # 1. 時間間隔の評価（理想的なサイクル時間: 0.6-1.2秒）
        duration = cycle['duration']
        if 0.6 <= duration <= 1.2:
            score += 30.0
        elif 0.4 <= duration <= 1.8:
            score += 20.0
        else:
            score += 10.0
        
        # 2. イベント順序の評価
        events = cycle['events']
        event_frames = [
            events['right_strike'],
            events['right_off'],
            events['left_strike'],
            events['left_off']
        ]
        
        # 順序が正しいかチェック
        if event_frames == sorted(event_frames):
            score += 25.0
        
        # 3. イベント間隔の均等性評価
        intervals = []
        for i in range(len(event_frames) - 1):
            intervals.append(event_frames[i + 1] - event_frames[i])
        
        if intervals:
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)
            if interval_mean > 0:
                cv = interval_std / interval_mean  # 変動係数
                if cv < 0.5:  # 間隔が比較的均等
                    score += 20.0
                elif cv < 1.0:
                    score += 10.0
        
        # 4. データ品質の評価（キーポイントの信頼度）
        start_frame = cycle['start_frame']
        end_frame = min(cycle['end_frame'], len(keypoints_data))
        
        confidence_scores = []
        for frame_idx in range(start_frame, end_frame):
            if frame_idx < len(keypoints_data):
                frame_data = keypoints_data[frame_idx]
                if 'keypoints' in frame_data:
                    keypoints = frame_data['keypoints']
                    # 足首の信頼度をチェック（インデックス27, 28）
                    if len(keypoints) > 28:
                        left_ankle_conf = keypoints[27].get('visibility', 0.5)
                        right_ankle_conf = keypoints[28].get('visibility', 0.5)
                        confidence_scores.append((left_ankle_conf + right_ankle_conf) / 2)
        
        if confidence_scores:
            avg_confidence = np.mean(confidence_scores)
            if avg_confidence > 0.8:
                score += 25.0
            elif avg_confidence > 0.6:
                score += 15.0
            elif avg_confidence > 0.4:
                score += 5.0
        
        return min(score, 100.0)  # 最大100点
        
    except Exception as e:
        print(f"   ⚠️  サイクル評価エラー: {e}")
        return 0.0

def calculate_cycle_event_angles(keypoints_data: List[Dict], cycle: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    選択されたサイクルの各イベント時の角度を計算
    部分サイクル対応: Noneのイベントはスキップ
    
    Args:
        keypoints_data: キーポイントデータ
        cycle: 選択されたサイクル情報
    
    Returns:
        Dict: 各イベントの角度データ（Noneイベントは含まれない）
    """
    cycle_angles = {}
    events = cycle['events']
    is_partial = cycle.get('is_partial', False)
    
    # 各イベントの角度を計算
    event_mapping = {
        'right_strike': 'right_strike',
        'right_off': 'right_off', 
        'left_strike': 'left_strike',
        'left_off': 'left_off'
    }
    
    for event_key, angle_key in event_mapping.items():
        frame_idx = events.get(event_key)
        
        # Noneイベントはスキップ（部分サイクル対応）
        if frame_idx is None:
            if is_partial:
                print(f"   ⏭️  {angle_key}: イベント未検出のためスキップ")
            else:
                cycle_angles[angle_key] = {}
                print(f"   ⚠️  {angle_key}: フレームがNone")
            continue
        
        print(f"🔧 処理中: {event_key} -> {angle_key}, フレーム: {frame_idx}, データ型: {type(frame_idx)}")
        
        # frame_idxが整数かどうかをチェック
        try:
            if isinstance(frame_idx, int) and 0 <= frame_idx < len(keypoints_data):
                print(f"🔧 keypoints_data[{frame_idx}] アクセス試行...")
                frame_data = keypoints_data[frame_idx]
                print(f"🔧 フレームデータ取得成功: {type(frame_data)}")
                
                angles = calculate_angles_for_frame(frame_data)
                if angles:  # 空の角度データはスキップ
                    cycle_angles[angle_key] = angles
                    print(f"   📐 {angle_key} (フレーム{frame_idx}): 角度計算完了")
                else:
                    print(f"   ⚠️  {angle_key} (フレーム{frame_idx}): 角度計算結果が空（キーポイント不足の可能性）")
            else:
                print(f"   ⚠️  {angle_key}: フレーム{frame_idx}が無効（型: {type(frame_idx)}, 値: {frame_idx}）")
        except Exception as e:
            print(f"   ❌ {angle_key}: フレーム{frame_idx}でエラー - {type(e).__name__}: {e}")
    
    print(f"   📊 角度計算結果: {len(cycle_angles)}イベント分の角度を取得")
    return cycle_angles


def validate_and_filter_events(events: list, total_frames: int, video_fps: float) -> list:
    """
    偽イベントを検証・除外する（Cプラン: サイクル要件の緩和）
    
    除外条件:
    1. 動画の端10%以内のイベント（ランナー出入りの境界アーティファクト）
    2. 同側のstrike/offが1フレーム差以内（物理的に不可能）
    3. 左右のstrikeが2フレーム以内に連続（走行では物理的に不自然）
    
    Args:
        events: [(frame, side, type), ...] のリスト
        total_frames: 動画の総フレーム数
        video_fps: フレームレート
    
    Returns:
        フィルタ後のイベントリスト
    """
    if not events or not isinstance(events, list):
        return events
    
    original_count = len(events)
    
    # === フィルタ1: 動画端のイベント除外 ===
    margin = max(3, int(total_frames * 0.10))
    filtered = []
    for event in events:
        frame_num = event[0]
        if margin <= frame_num <= (total_frames - margin):
            filtered.append(event)
        else:
            print(f"   🚫 境界フィルタ: フレーム{frame_num} ({event[1]} {event[2]}) 除外 - 動画端{margin}フレーム以内")
    
    # === フィルタ2: 同側strike/offの間隔チェック ===
    # strike直後の同側offは最低3フレーム以上離れているべき
    validated = []
    for i, event in enumerate(filtered):
        is_suspicious = False
        for j, other in enumerate(filtered):
            if i == j:
                continue
            # 同側で異なるタイプ（strike vs off）のイベント
            if event[1] == other[1] and event[2] != other[2]:
                frame_diff = abs(event[0] - other[0])
                if frame_diff <= 1:
                    is_suspicious = True
                    print(f"   🚫 間隔フィルタ: フレーム{event[0]} ({event[1]} {event[2]}) 除外 - 同側イベントと{frame_diff}フレーム差")
                    break
        if not is_suspicious:
            validated.append(event)
    
    # === フィルタ3: 左右の同種イベント同時性チェック ===
    # 左右のstrike/offが2フレーム以内に同時発生は非現実的
    final = []
    removed_indices = set()
    
    for event_type in ['strike', 'off']:
        typed_events = [(e, i) for i, e in enumerate(validated) if e[2] == event_type]
        for i in range(len(typed_events)):
            for j in range(i + 1, len(typed_events)):
                e1, idx1 = typed_events[i]
                e2, idx2 = typed_events[j]
                if e1[1] != e2[1]:  # 左右が異なる
                    frame_diff = abs(e1[0] - e2[0])
                    if frame_diff <= 2:
                        # 両方除外
                        removed_indices.add(idx1)
                        removed_indices.add(idx2)
                        print(f"   🚫 同時{event_type}: フレーム{e1[0]}({e1[1]}) と フレーム{e2[0]}({e2[1]}) 除外 - {frame_diff}フレーム差")
    
    for i, event in enumerate(validated):
        if i not in removed_indices:
            final.append(event)
    
    removed_count = original_count - len(final)
    if removed_count > 0:
        print(f"   📊 イベント検証結果: {original_count}個 → {len(final)}個 ({removed_count}個除外)")
    else:
        print(f"   ✅ イベント検証: 全{original_count}個が有効")
    
    return final


def find_best_quality_frame(keypoints_data: List[Dict]) -> Optional[int]:
    """
    キーポイント品質が最も高いフレームを見つける（最終フォールバック用）
    
    Args:
        keypoints_data: キーポイントデータ
    
    Returns:
        最高品質フレームのインデックス、またはNone
    """
    best_frame = None
    best_score = 0
    
    # 主要キーポイント（肩、腰、膝、足首）
    key_indices = [11, 12, 23, 24, 25, 26, 27, 28]
    
    for i, frame_data in enumerate(keypoints_data):
        if 'keypoints' not in frame_data:
            continue
        kps = frame_data['keypoints']
        if len(kps) < 33:
            continue
        
        # 主要キーポイントのvisibilityの合計をスコアとする
        score = sum(kps[idx].get('visibility', 0) for idx in key_indices if idx < len(kps))
        
        if score > best_score:
            best_score = score
            best_frame = i
    
    if best_frame is not None:
        print(f"   🔍 最高品質フレーム検索: フレーム{best_frame}, スコア={best_score:.2f}/8.0")
    
    return best_frame

# =============================================================================
# Z値分析メイン関数
# =============================================================================
def analyze_form_with_z_scores(all_keypoints: List[Dict], video_fps: float) -> Dict[str, Any]:
    """
    Z値で解析するメイン関数（ワンサイクル解析版）
    
    Args:
        all_keypoints: ユーザーの動画全体のキーポイントデータ
        video_fps: 動画のフレームレート
    
    Returns:
        Dict: Z値分析結果
    """
    try:
        print("🎯 ワンサイクル Z値分析を開始します...")
        print(f"🔧 入力データ確認: all_keypoints型={type(all_keypoints)}, 長さ={len(all_keypoints) if hasattr(all_keypoints, '__len__') else 'unknown'}")
        print(f"🔧 video_fps={video_fps}")
        
        # 1. 標準モデルデータを取得
        print("🔧 標準モデルデータ取得開始")
        standard_model = get_event_based_standard_model()
        print("🔧 標準モデルデータ取得完了")
        
        # 2. 足接地・離地を検出
        print("🔧 detect_foot_strikes_advanced 呼び出し開始")
        all_events = detect_foot_strikes_advanced(all_keypoints, video_fps)
        print(f"🔧 detect_foot_strikes_advanced 呼び出し完了: {len(all_events)}個のイベント検出（フィルタ前）")
        
        # 2.5. 偽イベント検証: 動画の端付近・物理的に不可能なイベントを除外
        total_frames = len(all_keypoints)
        all_events = validate_and_filter_events(all_events, total_frames, video_fps)
        print(f"🔧 イベント検証後: {len(all_events)}個のイベント残存")
        
        # 3. all_eventsをリストから辞書形式に変換
        print("🔧 all_eventsをリストから辞書形式に変換開始")
        events_dict = convert_events_list_to_dict(all_events)
        print(f"🔧 変換完了: {events_dict}")
        
        # 4. 最良のワンサイクルを特定
        print("🔧 identify_best_running_cycle 呼び出し開始")
        best_cycle = identify_best_running_cycle(events_dict, all_keypoints, video_fps)
        print(f"🔧 identify_best_running_cycle 呼び出し完了: best_cycle={best_cycle is not None}")
        
        if not best_cycle:
            print("⚠️  明確なランニングサイクルが見つかりませんでした")
            print("🔧 Cプラン: 部分イベントでもZ値分析を実行します")
            
            total_frames = len(all_keypoints)
            
            if isinstance(all_events, list) and len(all_events) > 0:
                print(f"   📊 検出されたイベント数: {len(all_events)}")
                print(f"   📝 イベント詳細: {all_events}")
                
                # === 偽イベント検証: 動画の端10%以内のイベントを除外 ===
                margin = max(3, int(total_frames * 0.10))
                validated_events = []
                for event in all_events:
                    frame_num = event[0]
                    if margin <= frame_num <= (total_frames - margin):
                        validated_events.append(event)
                    else:
                        print(f"   🚫 偽イベント除外: フレーム{frame_num} ({event[1]} {event[2]}) - 動画端付近")
                
                excluded_count = len(all_events) - len(validated_events)
                if excluded_count > 0:
                    print(f"   📊 偽イベント除外: {excluded_count}個除外, {len(validated_events)}個残存")
                
                # 検証後のイベントを使用
                if len(validated_events) > 0:
                    right_strikes = [e[0] for e in validated_events if e[1] == 'right' and e[2] == 'strike']
                    right_offs = [e[0] for e in validated_events if e[1] == 'right' and e[2] == 'off']
                    left_strikes = [e[0] for e in validated_events if e[1] == 'left' and e[2] == 'strike']
                    left_offs = [e[0] for e in validated_events if e[1] == 'left' and e[2] == 'off']
                    
                    # === 部分サイクル: 検出できたイベントだけで分析 ===
                    partial_events = {
                        'right_strike': int(right_strikes[0]) if right_strikes else None,
                        'right_off': int(right_offs[0]) if right_offs else None,
                        'left_strike': int(left_strikes[0]) if left_strikes else None,
                        'left_off': int(left_offs[0]) if left_offs else None
                    }
                    
                    # None以外のイベント数をカウント
                    valid_event_count = sum(1 for v in partial_events.values() if v is not None)
                    
                    if valid_event_count > 0:
                        valid_frames = [v for v in partial_events.values() if v is not None]
                        alternative_cycle = {
                            'start_frame': min(valid_frames),
                            'end_frame': max(valid_frames),
                            'events': partial_events,
                            'is_partial': True
                        }
                        print(f"✅ 部分サイクルで分析を継続します（{valid_event_count}/4イベント）")
                        print(f"   📋 部分サイクル: {partial_events}")
                        best_cycle = alternative_cycle
                    else:
                        print("❌ 偽イベント除外後、有効なイベントが残りませんでした")
                else:
                    print("❌ 偽イベント除外後、有効なイベントが残りませんでした")
            
            # それでもbest_cycleがない場合はエラー
            if not best_cycle:
                # 最終フォールバック: キーポイント品質が高いフレームを直接選んで分析
                print("🔧 最終フォールバック: 高品質フレームから直接角度を推定します")
                best_frame = find_best_quality_frame(all_keypoints)
                if best_frame is not None:
                    print(f"   ✅ 最高品質フレーム: {best_frame}")
                    # 単一フレームを全イベントとして使用（精度は低いが分析は可能）
                    best_cycle = {
                        'start_frame': best_frame,
                        'end_frame': best_frame,
                        'events': {
                            'right_strike': best_frame,
                            'right_off': None,
                            'left_strike': None,
                            'left_off': None
                        },
                        'is_partial': True,
                        'is_single_frame_fallback': True
                    }
                else:
                    return {
                        'error': '分析可能なイベントが不足しています',
                        'events_detected': all_events if isinstance(all_events, list) else str(all_events),
                        'event_angles': {},
                        'z_scores': {},
                        'analysis_summary': {}
                    }
        
        # 4. 選択されたサイクルのイベント角度を計算
        print(f"🔧 サイクル情報をデバッグ: {best_cycle}")
        print(f"🔧 キーポイントデータ型: {type(all_keypoints)}, サイズ: {len(all_keypoints) if hasattr(all_keypoints, '__len__') else 'unknown'}")
        
        # 代替サイクルのevents値を詳細チェック
        if best_cycle and 'events' in best_cycle:
            for event_name, frame_idx in best_cycle['events'].items():
                print(f"🔧 イベント詳細チェック: {event_name} = {frame_idx} (型: {type(frame_idx)})")
        
        try:
            print("🔧 calculate_cycle_event_angles 関数呼び出し開始")
            cycle_event_angles = calculate_cycle_event_angles(all_keypoints, best_cycle)
            print("🔧 calculate_cycle_event_angles 関数呼び出し成功")
        except Exception as e:
            print(f"❌ calculate_cycle_event_angles でエラー発生: {type(e).__name__}: {e}")
            import traceback
            print(f"🔍 完全なスタックトレース:")
            traceback.print_exc()
            print(f"🔧 エラー発生時のbest_cycle: {best_cycle}")
            return {
                'error': f'cycle_event_angles計算エラー: {str(e)}',
                'events_detected': all_events,
                'event_angles': {},
                'z_scores': {},
                'analysis_summary': {}
            }
        
        # 5. Z値を計算
        z_scores = calculate_z_scores(cycle_event_angles, standard_model)
        
        # 6. 分析結果を整理
        analysis_result = {
            'events_detected': all_events,
            'selected_cycle': best_cycle,
            'event_angles': cycle_event_angles,
            'z_scores': z_scores,
            'analysis_summary': generate_analysis_summary(z_scores)
        }
        
        print("✅ ワンサイクル Z値分析が完了しました")
        return analysis_result
        
    except Exception as e:
        print(f"❌ Z値分析エラー: {type(e).__name__}: {e}")
        import traceback
        print(f"🔍 詳細なスタックトレース:")
        traceback.print_exc()
        
        # エラーの詳細な情報を出力
        print(f"🔧 エラー発生時の変数状態:")
        try:
            print(f"   - all_keypoints型: {type(all_keypoints)}")
            print(f"   - all_keypoints長さ: {len(all_keypoints) if hasattr(all_keypoints, '__len__') else 'unknown'}")
            print(f"   - video_fps: {video_fps}")
        except Exception as debug_e:
            print(f"   - デバッグ情報取得エラー: {debug_e}")
        
        return {
            'error': str(e),
            'events_detected': {},
            'selected_cycle': None,
            'event_angles': {},
            'z_scores': {},
            'analysis_summary': {}
        }

def calculate_angles_for_frame(frame_data: Dict) -> Dict[str, float]:
    """
    単一フレームの角度を計算
    
    Args:
        frame_data: フレームデータ
    
    Returns:
        Dict: 角度データ
    """
    try:
        if 'keypoints' not in frame_data:
            return {}
        
        keypoints = frame_data['keypoints']
        if len(keypoints) < 33:  # MediaPipeの最小キーポイント数
            return {}
        
        # キーポイントインデックス（MediaPipe Pose）
        landmarks = {
            'nose': 0, 'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8, 'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12, 'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16, 'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20, 'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24, 'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28, 'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
        
        # 体幹角度（肩と腰の中点の角度）
        trunk_angle = calculate_trunk_angle_from_keypoints(keypoints, landmarks)
        
        # 大腿角度（左右）
        left_thigh_angle = calculate_thigh_angle_from_keypoints(keypoints, landmarks, 'left')
        right_thigh_angle = calculate_thigh_angle_from_keypoints(keypoints, landmarks, 'right')
        
        # 下腿角度（左右）
        left_lower_leg_angle = calculate_lower_leg_angle_from_keypoints(keypoints, landmarks, 'left')
        right_lower_leg_angle = calculate_lower_leg_angle_from_keypoints(keypoints, landmarks, 'right')
        
        return {
            '体幹角度': trunk_angle,
            '左大腿角度': left_thigh_angle,
            '右大腿角度': right_thigh_angle,
            '左下腿角度': left_lower_leg_angle,
            '右下腿角度': right_lower_leg_angle
        }
        
    except Exception as e:
        print(f"❌ 角度計算エラー: {e}")
        return {}

def calculate_trunk_angle_from_keypoints(keypoints: List[Dict], landmarks: Dict) -> float:
    """体幹角度を計算"""
    try:
        print(f"🔧 keypoints型: {type(keypoints)}, 長さ: {len(keypoints) if hasattr(keypoints, '__len__') else 'unknown'}")
        print(f"🔧 keypoints[0]型: {type(keypoints[0]) if keypoints else 'empty'}")
        print(f"🔧 landmarks: {landmarks}")
        print(f"🔧 left_shoulder index: {landmarks['left_shoulder']}")
        
        # 肩の中点
        left_shoulder = keypoints[landmarks['left_shoulder']]
        right_shoulder = keypoints[landmarks['right_shoulder']]
        shoulder_mid = {
            'x': (left_shoulder['x'] + right_shoulder['x']) / 2,
            'y': (left_shoulder['y'] + right_shoulder['y']) / 2
        }
        
        # 腰の中点
        left_hip = keypoints[landmarks['left_hip']]
        right_hip = keypoints[landmarks['right_hip']]
        hip_mid = {
            'x': (left_hip['x'] + right_hip['x']) / 2,
            'y': (left_hip['y'] + right_hip['y']) / 2
        }
        
        # 体幹ベクトル
        trunk_vector = np.array([hip_mid['x'] - shoulder_mid['x'], hip_mid['y'] - shoulder_mid['y']])
        
        # 鉛直軸との角度
        vertical_vector = np.array([0, 1])
        angle = calculate_angle_between_vectors(trunk_vector, vertical_vector)
        
        return angle if angle is not None else 0.0
        
    except Exception:
        return 0.0

def calculate_thigh_angle_from_keypoints(keypoints: List[Dict], landmarks: Dict, side: str) -> float:
    """大腿角度を計算"""
    try:
        if side == 'left':
            hip = keypoints[landmarks['left_hip']]
            knee = keypoints[landmarks['left_knee']]
        else:
            hip = keypoints[landmarks['right_hip']]
            knee = keypoints[landmarks['right_knee']]
        
        # 大腿ベクトル
        thigh_vector = np.array([knee['x'] - hip['x'], knee['y'] - hip['y']])
        
        # 鉛直軸との角度
        vertical_vector = np.array([0, 1])
        angle = calculate_angle_between_vectors(thigh_vector, vertical_vector)
        
        # 左右の符号調整
        if side == 'left':
            return angle if angle is not None else 0.0
        else:
            return -angle if angle is not None else 0.0
            
    except Exception:
        return 0.0

def calculate_lower_leg_angle_from_keypoints(keypoints: List[Dict], landmarks: Dict, side: str) -> float:
    """
    下腿角度を計算（画像の定義に基づく正しい計算方法）
    定義: 下腿ベクトル（足首→膝）と鉛直軸がなす角度
    符号規則: 鉛直軸に対して右側（後方）がマイナス、左側（前方）がプラス
    ・足首が膝より後方（離地時）で正値（左側）
    ・足首が膝より前方（接地時）で負値（右側）
    """
    try:
        if side == 'left':
            knee = keypoints[landmarks['left_knee']]
            ankle = keypoints[landmarks['left_ankle']]
        else:
            knee = keypoints[landmarks['right_knee']]
            ankle = keypoints[landmarks['right_ankle']]
        
        # 下腿ベクトル（足首→膝）
        lower_leg_vector = np.array([knee['x'] - ankle['x'], knee['y'] - ankle['y']])
        
        # 鉛直軸との角度を計算
        length = np.linalg.norm(lower_leg_vector)
        if length == 0:
            return 0.0
        
        # atan2(x, -y) は y軸負方向（上向き）からの角度を計算
        # 画像座標系ではyが下向きが正なので、-yが上向き
        angle_rad = np.arctan2(lower_leg_vector[0], -lower_leg_vector[1])
        angle_deg = np.degrees(angle_rad)
        
        # 90度の補角を取ってしまっている問題を修正
        # 83.58度 → 6.42度（90 - 83.58）、87.75度 → 2.25度（90 - 87.75）
        # 角度が90度に近い場合（|angle_deg| > 45度）、補角を取る
        if abs(angle_deg) > 45:
            # 90度の補角を計算（符号を保持）
            # 符号規則: 右側（後方）がマイナス、左側（前方）がプラス
            if angle_deg > 0:
                angle_deg = 90 - angle_deg
            else:
                angle_deg = -90 - angle_deg
        
        return angle_deg
            
    except Exception:
        return 0.0

def calculate_angle_between_vectors(vec1: np.ndarray, vec2: np.ndarray) -> Optional[float]:
    """2つのベクトル間の角度を計算"""
    try:
        # 内積を計算
        dot_product = np.dot(vec1, vec2)
        
        # ベクトルの大きさを計算
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return None
        
        # 角度を計算（ラジアンから度に変換）
        cos_angle = dot_product / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # 数値誤差を防ぐ
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
        
    except Exception:
        return None

def calculate_z_scores(event_angles: Dict[str, Dict[str, float]], standard_model: Dict) -> Dict[str, Dict[str, float]]:
    """
    Z値を計算
    
    Args:
        event_angles: 各イベントの角度データ
        standard_model: 標準モデルデータ
    
    Returns:
        Dict: 各イベント・各指標のZ値
    """
    z_scores = {}
    
    print("\n" + "=" * 100)
    print("🧮 Z値計算の詳細表示")
    print("=" * 100)
    
    for event_type, angles in event_angles.items():
        if event_type not in standard_model or not angles:
            continue
            
        z_scores[event_type] = {}
        standard_data = standard_model[event_type]
        
        print(f"\n📊 【{event_type}】イベントのZ値計算:")
        print("-" * 80)
        
        for angle_name, angle_value in angles.items():
            if angle_name in standard_data:
                mean = standard_data[angle_name]['mean']
                std = standard_data[angle_name]['std']
                
                if std > 0:
                    z_score = (angle_value - mean) / std
                    z_scores[event_type][angle_name] = z_score
                    
                    print(f"📐 {angle_name}:")
                    print(f"   ユーザー値: {angle_value:.2f}°")
                    print(f"   標準平均値: {mean:.4f}°")
                    print(f"   標準偏差  : {std:.4f}°")
                    print(f"   計算式    : ({angle_value:.2f} - {mean:.4f}) / {std:.4f}")
                    print(f"   Z値      : {z_score:.2f}")
                    
                    # 評価コメント
                    if abs(z_score) <= 1.0:
                        comment = "✅ 正常範囲内"
                    elif abs(z_score) <= 1.5:
                        comment = "⚠️  やや偏差あり"
                    else:
                        comment = "🚨 大きな偏差"
                    print(f"   評価      : {comment}")
                    print()
                else:
                    z_scores[event_type][angle_name] = 0.0
                    print(f"📐 {angle_name}: 標準偏差が0のためZ値計算不可")
    
    print("=" * 100)
    return z_scores

def generate_analysis_summary(z_scores: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    分析結果のサマリーを生成
    
    Args:
        z_scores: Z値データ
    
    Returns:
        Dict: 分析サマリー
    """
    summary = {
        'total_events_analyzed': len(z_scores),
        'significant_deviations': [],
        'overall_assessment': 'normal',
        'recommendations': []
    }
    
    # 有意な偏差を検出（|Z| > 1.5）
    for event_type, scores in z_scores.items():
        for angle_name, z_score in scores.items():
            if abs(z_score) > 1.5:
                summary['significant_deviations'].append({
                    'event': event_type,
                    'angle': angle_name,
                    'z_score': z_score,
                    'severity': 'high' if abs(z_score) > 2.5 else 'moderate'
                })
    
    # 全体評価
    if len(summary['significant_deviations']) == 0:
        summary['overall_assessment'] = 'excellent'
    elif len(summary['significant_deviations']) <= 2:
        summary['overall_assessment'] = 'good'
    elif len(summary['significant_deviations']) <= 4:
        summary['overall_assessment'] = 'needs_improvement'
    else:
        summary['overall_assessment'] = 'significant_issues'
    
    return summary

def print_z_score_analysis_results(analysis_result: Dict[str, Any]) -> None:
    """
    Z値分析結果を分かりやすい表形式でコンソールに出力
    
    Args:
        analysis_result: Z値分析結果
    """
    print("\n" + "="*80)
    print("🎯 イベント別Z値フォーム分析結果")
    print("="*80)
    
    if 'error' in analysis_result:
        print(f"❌ エラー: {analysis_result['error']}")
        return
    
    z_scores = analysis_result.get('z_scores', {})
    analysis_summary = analysis_result.get('analysis_summary', {})
    
    # イベント名の日本語変換
    event_names = {
        'right_strike': '右足接地',
        'right_off': '右足離地',
        'left_strike': '左足接地',
        'left_off': '左足離地'
    }
    
    # 角度名の日本語変換
    angle_names = {
        '体幹角度': '体幹角度',
        '左大腿角度': '左大腿角度',
        '右大腿角度': '右大腿角度',
        '左下腿角度': '左下腿角度',
        '右下腿角度': '右下腿角度'
    }
    
    # 各イベントのZ値を表示
    for event_type, scores in z_scores.items():
        event_name = event_names.get(event_type, event_type)
        print(f"\n📊 {event_name}")
        print("-" * 50)
        
        if not scores:
            print("   ⚠️  データなし")
            continue
            
        for angle_name, z_score in scores.items():
            angle_display = angle_names.get(angle_name, angle_name)
            
            # Z値の評価
            if abs(z_score) > 2.5:
                status = "🔴 要改善"
                color = "\033[91m"  # 赤
            elif abs(z_score) > 1.5:
                status = "🟡 注意"
                color = "\033[93m"  # 黄
            elif abs(z_score) > 1.0:
                status = "🟢 良好"
                color = "\033[92m"  # 緑
            else:
                status = "✅ 優秀"
                color = "\033[94m"  # 青
            
            # 色付きで表示
            print(f"   {angle_display:12s}: {color}Z={z_score:+6.2f}\033[0m {status}")
    
    # 全体サマリー
    print("\n" + "="*80)
    print("📈 分析サマリー")
    print("="*80)
    
    total_events = analysis_summary.get('total_events_analyzed', 0)
    significant_deviations = analysis_summary.get('significant_deviations', [])
    overall_assessment = analysis_summary.get('overall_assessment', 'unknown')
    
    print(f"分析イベント数: {total_events}")
    print(f"有意な偏差数: {len(significant_deviations)}")
    
    # 全体評価
    assessment_text = {
        'excellent': '✅ 優秀 - 標準的なフォームです',
        'good': '🟢 良好 - 軽微な改善点があります',
        'needs_improvement': '🟡 要改善 - 複数の改善点があります',
        'significant_issues': '🔴 要改善 - 多くの改善点があります',
        'normal': '⚪ 通常 - 分析結果を確認してください'
    }
    
    print(f"全体評価: {assessment_text.get(overall_assessment, overall_assessment)}")
    
    # 有意な偏差の詳細
    if significant_deviations:
        print(f"\n⚠️  注目すべき点 (|Z| > 1.5):")
        for i, deviation in enumerate(significant_deviations, 1):
            event_name = event_names.get(deviation['event'], deviation['event'])
            angle_name = angle_names.get(deviation['angle'], deviation['angle'])
            severity = "🔴 高" if deviation['severity'] == 'high' else "🟡 中"
            
            print(f"   {i}. {event_name} - {angle_name}: Z={deviation['z_score']:+6.2f} ({severity})")
    else:
        print("\n✅ 有意な偏差は検出されませんでした - 優秀なフォームです！")
    
    print("\n" + "="*80)
    print("💡 Z値の読み方:")
    print("   |Z| < 1.0: 標準範囲内")
    print("   1.0 ≤ |Z| < 1.5: やや標準から外れている")
    print("   1.5 ≤ |Z| < 2.5: 標準から大きく外れている（注意・改善推奨）")
    print("   |Z| ≥ 2.5: 標準から非常に大きく外れている（要改善）")
    print("="*80)

def print_all_events_summary(all_events: List[Tuple[int, str, str]]) -> None:
    """
    全イベントのサマリーを表示
    
    Args:
        all_events: (フレーム番号, 足, イベント種類) のリスト
    """
    if not all_events:
        return
    
    print("\n" + "="*80)
    print("🎯 全イベント検出サマリー（時系列順）")
    print("="*80)
    
    for i, (frame, foot, event_type) in enumerate(all_events, 1):
        event_emoji = "🦶" if event_type == "strike" else "🚁"
        foot_name = "左足" if foot == "left" else "右足"
        event_name = "接地" if event_type == "strike" else "離地"
        
        print(f"   {i:2d}. フレーム{frame:3d}: {event_emoji} {foot_name}{event_name}")
    
    print(f"\n📊 検出統計:")
    left_strikes = len([e for e in all_events if e[1] == 'left' and e[2] == 'strike'])
    left_offs = len([e for e in all_events if e[1] == 'left' and e[2] == 'off'])
    right_strikes = len([e for e in all_events if e[1] == 'right' and e[2] == 'strike'])
    right_offs = len([e for e in all_events if e[1] == 'right' and e[2] == 'off'])
    
    print(f"   左足: 接地{left_strikes}回, 離地{left_offs}回")
    print(f"   右足: 接地{right_strikes}回, 離地{right_offs}回")
    print(f"   合計: {len(all_events)}イベント")
    print("="*80)

def print_selected_cycle_info(cycle: Dict[str, Any]) -> None:
    """
    選択されたサイクルの詳細情報を表示
    
    Args:
        cycle: 選択されたサイクル情報
    """
    print("\n" + "="*80)
    print("🏆 選択されたワンサイクル詳細")
    print("="*80)
    
    print(f"📅 期間: フレーム{cycle['start_frame']}-{cycle['end_frame']}")
    # durationキーが存在する場合のみ表示
    duration = cycle.get('duration', 0)
    if duration > 0:
        print(f"⏱️  時間: {duration:.3f}秒")
    else:
        print("⏱️  時間: 計算中...")
    
    events = cycle['events']
    is_partial = cycle.get('is_partial', False)
    
    event_names = {
        'right_strike': '右足接地',
        'right_off': '右足離地',
        'left_strike': '左足接地',
        'left_off': '左足離地'
    }
    
    print(f"\n🎯 サイクル内イベント{'（部分サイクル）' if is_partial else ''}:")
    for i, (key, name) in enumerate(event_names.items(), 1):
        frame = events.get(key)
        if frame is not None:
            print(f"   {i}. {name}: フレーム{frame}")
        else:
            print(f"   {i}. {name}: 未検出")
    
    # イベント間隔を計算（Noneを含む場合は安全にスキップ）
    if all(events.get(k) is not None for k in ['right_strike', 'right_off', 'left_strike', 'left_off']):
        intervals = [
            events['right_off'] - events['right_strike'],
            events['left_strike'] - events['right_off'],
            events['left_off'] - events['left_strike']
        ]
        
        print(f"\n📊 イベント間隔:")
        print(f"   右足接地→離地: {intervals[0]}フレーム")
        print(f"   右足離地→左足接地: {intervals[1]}フレーム") 
        print(f"   左足接地→離地: {intervals[2]}フレーム")
    else:
        valid_count = sum(1 for v in events.values() if v is not None)
        print(f"\n📊 検出イベント数: {valid_count}/4（部分的な検出のため間隔は算出不可）")
    
    print("\n💡 このサイクルのデータを使用してZ値分析を実行しました")
    print("="*80)

# =============================================================================
# リクエスト・レスポンスのデータモデル
# =============================================================================
class ZScoreAnalysisRequest(BaseModel):
    """Z値分析リクエスト"""
    keypoints_data: List[Dict[str, Any]]
    video_fps: float

class ZScoreAnalysisResponse(BaseModel):
    """Z値分析レスポンス"""
    status: str
    message: str
    events_detected: List[Tuple[int, str, str]]
    event_angles: Dict[str, Dict[str, float]]
    z_scores: Dict[str, Dict[str, float]]
    analysis_summary: Dict[str, Any]

# =============================================================================
# API エンドポイント
# =============================================================================
@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {
        "status": "healthy", 
        "service": "z_score_analysis", 
        "version": "3.0.0",
        "description": "Z-Score Based Running Form Analysis Service"
    }

@app.post("/analyze-z-score", response_model=ZScoreAnalysisResponse)
async def analyze_running_form_z_score(request: ZScoreAnalysisRequest):
    """
    Z値によるランニングフォーム分析（メインエンドポイント）
    
    4つの主要イベント（右足接地、右足離地、左足接地、左足離地）ごとに
    各指標のZ値を算出・評価する高度な解析機能
    """
    try:
        print("🎯 Z値分析リクエストを受信しました")
        
        # Z値分析を実行
        analysis_result = analyze_form_with_z_scores(request.keypoints_data, request.video_fps)
        
        # 結果をコンソールに出力
        print_z_score_analysis_results(analysis_result)
        
        # 全イベントのソート済みリストも表示
        if 'events_detected' in analysis_result:
            print_all_events_summary(analysis_result['events_detected'])
        
        # 選択されたサイクル情報も表示
        if 'selected_cycle' in analysis_result and analysis_result['selected_cycle']:
            print_selected_cycle_info(analysis_result['selected_cycle'])
        
        # レスポンスを構築
        if 'error' in analysis_result:
            return ZScoreAnalysisResponse(
                status="error",
                message=f"Z値分析中にエラーが発生しました: {analysis_result['error']}",
                events_detected=[],
                event_angles={},
                z_scores={},
                analysis_summary={}
            )
        
        # analysis_resultが辞書形式かチェック
        if isinstance(analysis_result, dict):
            return ZScoreAnalysisResponse(
                status="success",
                message="Z値分析が正常に完了しました",
                events_detected=analysis_result.get('events_detected', []),
                event_angles=analysis_result.get('event_angles', {}),
                z_scores=analysis_result.get('z_scores', {}),
                analysis_summary=analysis_result.get('analysis_summary', {})
            )
        else:
            # analysis_resultがリスト形式の場合はエラーログ出力
            print(f"⚠️  analysis_resultが予期しない形式です: {type(analysis_result)}")
            print(f"   📝 内容: {str(analysis_result)[:200]}...")
            import traceback
            print("🔍 エラーのスタックトレース:")
            traceback.print_exc()
            return ZScoreAnalysisResponse(
                status="error",
                message=f"分析結果の構造が予期しない形式です - 形式: {type(analysis_result)}",
                events_detected=[],
                event_angles={},
                z_scores={},
                analysis_summary={}
        )
        
    except Exception as e:
        print(f"❌ Z値分析APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return ZScoreAnalysisResponse(
            status="error",
            message=f"Z値分析中に予期しないエラーが発生しました: {str(e)}",
            events_detected=[],
            event_angles={},
            z_scores={},
            analysis_summary={}
        )

if __name__ == "__main__":
    print("🚀 Z-Score Analysis Service v3.0.0 を起動中...")
    print("🎯 イベント別Z値によるランニングフォーム分析")
    print("🏆 ワンサイクル特定機能搭載")
    uvicorn.run(app, host="0.0.0.0", port=8004) 
