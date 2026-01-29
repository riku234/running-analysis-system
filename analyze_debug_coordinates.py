#!/usr/bin/env python3
"""デバッグ座標データを分析するスクリプト"""

import csv
import sys

def analyze_coordinates(csv_file_path):
    """CSVファイルを読み込んで分析"""
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f'📊 データ分析結果')
    print(f'総行数: {len(rows)}')
    if rows:
        last_frame = int(rows[-1]['frame_number'])
        print(f'総フレーム数: {last_frame + 1}')
    print()

    # 座標の範囲を確認
    raw_x_values = [float(r['raw_x']) for r in rows]
    raw_y_values = [float(r['raw_y']) for r in rows]
    raw_z_values = [float(r['raw_z']) for r in rows]

    filtered_x_values = [float(r['filtered_x']) for r in rows]
    filtered_y_values = [float(r['filtered_y']) for r in rows]
    filtered_z_values = [float(r['filtered_z']) for r in rows]

    print('📈 MediaPipe生データの範囲:')
    print(f'  X: {min(raw_x_values):.6f} ~ {max(raw_x_values):.6f} (範囲: {max(raw_x_values) - min(raw_x_values):.6f})')
    print(f'  Y: {min(raw_y_values):.6f} ~ {max(raw_y_values):.6f} (範囲: {max(raw_y_values) - min(raw_y_values):.6f})')
    print(f'  Z: {min(raw_z_values):.6f} ~ {max(raw_z_values):.6f} (範囲: {max(raw_z_values) - min(raw_z_values):.6f})')
    print()

    print('📈 OneEuroFilter後のデータの範囲:')
    print(f'  X: {min(filtered_x_values):.6f} ~ {max(filtered_x_values):.6f} (範囲: {max(filtered_x_values) - min(filtered_x_values):.6f})')
    print(f'  Y: {min(filtered_y_values):.6f} ~ {max(filtered_y_values):.6f} (範囲: {max(filtered_y_values) - min(filtered_y_values):.6f})')
    print(f'  Z: {min(filtered_z_values):.6f} ~ {max(filtered_z_values):.6f} (範囲: {max(filtered_z_values) - min(filtered_z_values):.6f})')
    print()

    # 差分の統計
    diff_x_values = [abs(float(r['diff_x'])) for r in rows if float(r['diff_x']) != 0]
    diff_y_values = [abs(float(r['diff_y'])) for r in rows if float(r['diff_y']) != 0]
    diff_z_values = [abs(float(r['diff_z'])) for r in rows if float(r['diff_z']) != 0]

    if diff_x_values:
        print('📊 フィルタ前後の差分（絶対値）:')
        print(f'  X: 平均={sum(diff_x_values)/len(diff_x_values):.6f}, 最大={max(diff_x_values):.6f}')
        print(f'  Y: 平均={sum(diff_y_values)/len(diff_y_values):.6f}, 最大={max(diff_y_values):.6f}')
        print(f'  Z: 平均={sum(diff_z_values)/len(diff_z_values):.6f}, 最大={max(diff_z_values):.6f}')
    print()

    # 特定のキーポイント（例：左足首=27）の推移を確認
    left_ankle_rows = [r for r in rows if r['keypoint_index'] == '27']
    if left_ankle_rows:
        print('🦶 左足首（キーポイント27）の座標推移（最初の10フレーム）:')
        for r in left_ankle_rows[:10]:
            frame_num = r['frame_number']
            raw_x = r['raw_x']
            raw_y = r['raw_y']
            raw_z = r['raw_z']
            filtered_x = r['filtered_x']
            filtered_y = r['filtered_y']
            filtered_z = r['filtered_z']
            diff_x = r['diff_x']
            diff_y = r['diff_y']
            diff_z = r['diff_z']
            print(f'  フレーム{frame_num}: raw=({raw_x}, {raw_y}, {raw_z}) filtered=({filtered_x}, {filtered_y}, {filtered_z}) diff=({diff_x}, {diff_y}, {diff_z})')
    
    # 0-1の範囲外の値をチェック
    print()
    print('⚠️  0-1の範囲外の値チェック:')
    raw_x_out_of_range = [r for r in rows if float(r['raw_x']) < 0 or float(r['raw_x']) > 1]
    raw_y_out_of_range = [r for r in rows if float(r['raw_y']) < 0 or float(r['raw_y']) > 1]
    raw_z_out_of_range = [r for r in rows if float(r['raw_z']) < -1 or float(r['raw_z']) > 1]  # Zは-1~1の範囲が一般的
    
    print(f'  MediaPipe生データ: X範囲外={len(raw_x_out_of_range)}, Y範囲外={len(raw_y_out_of_range)}, Z範囲外={len(raw_z_out_of_range)}')
    
    filtered_x_out_of_range = [r for r in rows if float(r['filtered_x']) < 0 or float(r['filtered_x']) > 1]
    filtered_y_out_of_range = [r for r in rows if float(r['filtered_y']) < 0 or float(r['filtered_y']) > 1]
    filtered_z_out_of_range = [r for r in rows if float(r['filtered_z']) < -1 or float(r['filtered_z']) > 1]
    
    print(f'  OneEuroFilter後: X範囲外={len(filtered_x_out_of_range)}, Y範囲外={len(filtered_y_out_of_range)}, Z範囲外={len(filtered_z_out_of_range)}')

if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'latest_debug_coordinates.csv'
    analyze_coordinates(csv_file)
