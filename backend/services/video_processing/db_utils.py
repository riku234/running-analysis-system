"""
データベース接続ユーティリティモジュール
PostgreSQL (RDS) への接続を管理します
"""

import os
import psycopg2
from dotenv import load_dotenv
from typing import Optional

# .envファイルから環境変数を読み込む
load_dotenv()


def get_db_connection() -> Optional[psycopg2.extensions.connection]:
    """
    PostgreSQLデータベースへの接続を確立する関数
    
    .envファイルから以下の環境変数を読み込みます:
    - DB_HOST: データベースのホスト名（RDSエンドポイント）
    - DB_PORT: データベースのポート番号（デフォルト: 5432）
    - DB_NAME: データベース名
    - DB_USER: データベースユーザー名
    - DB_PASSWORD: データベースパスワード
    
    Returns:
        psycopg2.extensions.connection: 接続成功時は接続オブジェクト
        None: 接続失敗時はNone
    
    Example:
        >>> conn = get_db_connection()
        >>> if conn:
        >>>     cursor = conn.cursor()
        >>>     cursor.execute("SELECT version();")
        >>>     print(cursor.fetchone())
        >>>     cursor.close()
        >>>     conn.close()
    """
    try:
        # 環境変数からデータベース接続情報を取得
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "5432")  # デフォルトは5432
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        # 必須パラメータの検証
        if not all([db_host, db_name, db_user, db_password]):
            missing = []
            if not db_host: missing.append("DB_HOST")
            if not db_name: missing.append("DB_NAME")
            if not db_user: missing.append("DB_USER")
            if not db_password: missing.append("DB_PASSWORD")
            
            print(f"❌ エラー: 必須の環境変数が設定されていません: {', '.join(missing)}")
            print("💡 .envファイルを確認してください")
            return None
        
        # データベースへの接続を確立
        print(f"🔌 データベースへの接続を試みています...")
        print(f"   ホスト: {db_host}")
        print(f"   ポート: {db_port}")
        print(f"   データベース: {db_name}")
        print(f"   ユーザー: {db_user}")
        
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            # 接続タイムアウト設定（秒）
            connect_timeout=10
        )
        
        print("✅ データベース接続成功!")
        return connection
        
    except psycopg2.OperationalError as e:
        print(f"❌ データベース接続エラー（OperationalError）:")
        print(f"   {str(e)}")
        print("\n💡 確認事項:")
        print("   1. .envファイルの接続情報が正しいか")
        print("   2. RDSインスタンスが起動しているか")
        print("   3. セキュリティグループでポート5432が開放されているか")
        print("   4. ネットワーク接続が正常か")
        return None
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー:")
        print(f"   {str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました:")
        print(f"   {type(e).__name__}: {str(e)}")
        return None


def test_connection():
    """
    データベース接続をテストする関数
    
    接続が成功すると、PostgreSQLのバージョン情報を表示します。
    """
    print("=" * 60)
    print("🧪 データベース接続テスト")
    print("=" * 60)
    
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # PostgreSQLバージョンを取得
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"\n📊 PostgreSQLバージョン:")
            print(f"   {version[0]}")
            
            # 現在の日時を取得
            cursor.execute("SELECT NOW();")
            current_time = cursor.fetchone()
            print(f"\n🕐 サーバー時刻:")
            print(f"   {current_time[0]}")
            
            cursor.close()
            conn.close()
            print("\n✅ 接続テスト完了!")
            
        except Exception as e:
            print(f"\n❌ テスト中にエラーが発生しました: {e}")
            if conn:
                conn.close()
    else:
        print("\n❌ 接続テスト失敗")
    
    print("=" * 60)


def save_analysis_results(run_id: str, results_dict: dict) -> bool:
    """
    解析結果をデータベースに保存する関数
    
    Args:
        run_id (str): 走行ID（動画のユニークID）
        results_dict (dict): 指標名と計算値の辞書
            例: {
                "ピッチ": 181.5,
                "重心上下動": 0.065,
                "体幹前傾角度": 5.2,
                "着地時膝角度": 142.3
            }
    
    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    
    Example:
        >>> results = {
        >>>     "ピッチ": 181.5,
        >>>     "重心上下動": 0.065,
        >>>     "体幹前傾角度": 5.2
        >>> }
        >>> success = save_analysis_results("abc-123-def", results)
        >>> if success:
        >>>     print("保存成功!")
    """
    conn = None
    cursor = None
    
    try:
        # データベースに接続
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、保存できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"💾 解析結果を保存します...")
        print(f"   走行ID: {run_id}")
        print(f"   保存する指標数: {len(results_dict)}")
        
        # 各指標をループ処理してINSERT
        saved_count = 0
        for metric_name, value in results_dict.items():
            try:
                # analysis_resultsテーブルにINSERT
                # 同じrun_idとmetric_nameの組み合わせが既に存在する場合は更新
                insert_sql = """
                    INSERT INTO analysis_results (run_id, metric_name, value, created_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (run_id, metric_name) 
                    DO UPDATE SET 
                        value = EXCLUDED.value,
                        updated_at = NOW()
                """
                
                cursor.execute(insert_sql, (run_id, metric_name, value))
                saved_count += 1
                print(f"   ✓ {metric_name}: {value}")
                
            except Exception as e:
                print(f"   ✗ {metric_name}の保存に失敗: {e}")
                # 個別のエラーは記録するが処理は続行
        
        # 変更を確定
        conn.commit()
        print(f"\n✅ {saved_count}/{len(results_dict)} 件の指標を保存しました")
        
        return saved_count > 0
        
    except psycopg2.Error as e:
        print(f"\n❌ データベースエラーが発生しました:")
        print(f"   {str(e)}")
        
        # エラーが発生した場合はロールバック
        if conn:
            try:
                conn.rollback()
                print("   変更を破棄（rollback）しました")
            except Exception as rollback_error:
                print(f"   ロールバックに失敗: {rollback_error}")
        
        return False
        
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました:")
        print(f"   {type(e).__name__}: {str(e)}")
        
        # エラーが発生した場合はロールバック
        if conn:
            try:
                conn.rollback()
                print("   変更を破棄（rollback）しました")
            except Exception as rollback_error:
                print(f"   ロールバックに失敗: {rollback_error}")
        
        return False
        
    finally:
        # カーソルと接続を閉じる
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 データベース接続を閉じました")


def create_run_record(video_id: str, user_id: str, video_path: str, 
                      original_filename: str, video_fps: float = None,
                      video_duration: float = None, total_frames: int = None) -> Optional[int]:
    """
    新しい走行記録をデータベースに作成する関数
    
    Args:
        video_id (str): 動画の一意なID
        user_id (str): ユーザーID
        video_path (str): 動画ファイルのパス
        original_filename (str): 元のファイル名
        video_fps (float, optional): 動画のFPS
        video_duration (float, optional): 動画の長さ（秒）
        total_frames (int, optional): 総フレーム数
    
    Returns:
        Optional[int]: 作成されたrun_id（整数）を返す。失敗時はNone
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、走行記録を作成できません")
            return None
        
        cursor = conn.cursor()
        
        print(f"📝 新しい走行記録を作成します...")
        print(f"   video_id: {video_id}")
        print(f"   user_id: {user_id}")
        
        insert_sql = """
            INSERT INTO runs (
                video_id, user_id, video_path, original_filename,
                video_fps, video_duration, total_frames, analysis_status, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'processing', NOW())
            RETURNING id
        """
        
        cursor.execute(insert_sql, (
            video_id, user_id, video_path, original_filename,
            video_fps, video_duration, total_frames
        ))
        run_id = cursor.fetchone()[0]
        
        conn.commit()
        print(f"✅ 走行記録を作成しました: run_id={run_id}")
        
        return run_id
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {str(e)}")
        if conn:
            conn.rollback()
        return None
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def save_keypoints_data(run_id: int, keypoints_data: list) -> bool:
    """
    キーポイントデータをデータベースに一括保存する関数
    
    Args:
        run_id (int): 走行ID
        keypoints_data (list): 全フレームのキーポイントデータ
            例: [
                {
                    "frame": 0,
                    "keypoints": [
                        {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.9},
                        ...
                    ]
                },
                ...
            ]
    
    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、キーポイントを保存できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"💾 キーポイントデータを保存します...")
        print(f"   run_id: {run_id}")
        print(f"   フレーム数: {len(keypoints_data)}")
        
        # MediaPipeのランドマーク名（33個）
        landmark_names = [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index"
        ]
        
        # 一括挿入用のデータリストを作成
        insert_data = []
        for frame_data in keypoints_data:
            frame_number = frame_data.get("frame", 0)
            keypoints = frame_data.get("keypoints", [])
            
            for landmark_id, kp in enumerate(keypoints):
                if landmark_id < len(landmark_names):
                    landmark_name = landmark_names[landmark_id]
                else:
                    landmark_name = f"landmark_{landmark_id}"
                
                insert_data.append((
                    run_id,
                    frame_number,
                    landmark_id,
                    landmark_name,
                    kp.get("x", 0.0),
                    kp.get("y", 0.0),
                    kp.get("z", 0.0),
                    kp.get("visibility", 0.0)
                ))
        
        # 一括挿入
        insert_sql = """
            INSERT INTO keypoints (
                run_id, frame_number, landmark_id, landmark_name,
                x_coordinate, y_coordinate, z_coordinate, visibility
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, frame_number, landmark_id) DO NOTHING
        """
        
        # バッチサイズで分割して挿入（メモリ効率化）
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(insert_data), batch_size):
            batch = insert_data[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)
            
            if (i // batch_size + 1) % 10 == 0:
                print(f"   進行状況: {total_inserted}/{len(insert_data)} レコード")
        
        conn.commit()
        print(f"✅ {total_inserted} 件のキーポイントを保存しました")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def save_events_data(run_id: int, events: list) -> bool:
    """
    イベントデータ（足接地・離地）をデータベースに保存する関数
    
    Args:
        run_id (int): 走行ID
        events (list): イベントデータ
            例: [(frame, 'left', 'strike'), (frame, 'right', 'off'), ...]
    
    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、イベントを保存できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"💾 イベントデータを保存します...")
        print(f"   run_id: {run_id}")
        print(f"   イベント数: {len(events)}")
        
        insert_sql = """
            INSERT INTO events (run_id, frame_number, foot_side, event_type)
            VALUES (%s, %s, %s, %s)
        """
        
        insert_data = []
        for event in events:
            if len(event) >= 3:
                frame_number, foot_side, event_type = event[0], event[1], event[2]
                insert_data.append((run_id, frame_number, foot_side, f"{foot_side}_{event_type}"))
        
        cursor.executemany(insert_sql, insert_data)
        conn.commit()
        
        print(f"✅ {len(insert_data)} 件のイベントを保存しました")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_run_status(run_id: int, status: str) -> bool:
    """
    走行記録のステータスを更新する関数
    
    Args:
        run_id (int): 走行ID
        status (str): 新しいステータス ('processing', 'completed', 'failed')
    
    Returns:
        bool: 更新成功時はTrue、失敗時はFalse
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、ステータスを更新できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"🔄 走行記録のステータスを更新します...")
        print(f"   run_id: {run_id}")
        print(f"   新しいステータス: {status}")
        
        update_sql = """
            UPDATE runs 
            SET analysis_status = %s, updated_at = NOW()
            WHERE id = %s
        """
        
        cursor.execute(update_sql, (status, run_id))
        
        if cursor.rowcount == 0:
            print(f"⚠️  run_id={run_id}のレコードが見つかりませんでした")
            conn.rollback()
            return False
        
        conn.commit()
        print(f"✅ ステータスを'{status}'に更新しました")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def save_analysis_results(run_id: int, results_dict: dict) -> bool:
    """
    解析結果をデータベースに保存する関数
    
    Args:
        run_id (int): 走行ID
        results_dict (dict): 解析結果の辞書
            例: {
                "ピッチ": 181.5,
                "重心上下動": 0.065,
                "Z値_右足接地_体幹角度": -1.23,
                ...
            }
    
    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、解析結果を保存できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"💾 解析結果を保存します...")
        print(f"   run_id: {run_id}")
        print(f"   指標数: {len(results_dict)}")
        
        insert_sql = """
            INSERT INTO analysis_results (run_id, metric_name, value, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (run_id, metric_name) 
            DO UPDATE SET 
                value = EXCLUDED.value,
                updated_at = NOW()
        """
        
        saved_count = 0
        for metric_name, value in results_dict.items():
            try:
                # 数値に変換可能かチェック
                numeric_value = float(value) if value is not None else 0.0
                cursor.execute(insert_sql, (run_id, metric_name, numeric_value))
                saved_count += 1
            except (ValueError, TypeError) as e:
                print(f"   ⚠️  {metric_name}の値が数値ではありません: {value}")
                continue
        
        conn.commit()
        print(f"✅ {saved_count}/{len(results_dict)} 件の解析結果を保存しました")
        
        return saved_count > 0
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # このファイルを直接実行した場合は接続テストを実行
    test_connection()
    
    # 保存機能のテスト（オプション）
    print("\n" + "=" * 60)
    print("🧪 保存機能テスト")
    print("=" * 60)
    
    # テストデータ
    test_run_id = "test-run-001"
    test_results = {
        "ピッチ": 181.5,
        "重心上下動": 0.065,
        "体幹前傾角度": 5.2,
        "着地時膝角度": 142.3,
        "滞空時間": 0.15
    }
    
    print(f"\n📝 テストデータで保存を試みます...")
    success = save_analysis_results(test_run_id, test_results)
    
    if success:
        print("\n✅ 保存テスト成功!")
    else:
        print("\n❌ 保存テスト失敗")
    
    print("=" * 60)

