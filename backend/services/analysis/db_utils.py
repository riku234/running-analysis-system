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


def create_new_run(user_id: str, video_path: str) -> Optional[str]:
    """
    新しい走行記録をデータベースに作成する関数
    
    Args:
        user_id (str): ユーザーID
        video_path (str): 動画ファイルのパス
    
    Returns:
        Optional[str]: 作成されたrun_idを返す。失敗時はNone
    
    Example:
        >>> run_id = create_new_run("user123", "/uploads/video.mp4")
        >>> if run_id:
        >>>     print(f"走行記録を作成しました: {run_id}")
    """
    conn = None
    cursor = None
    
    try:
        # データベースに接続
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、走行記録を作成できません")
            return None
        
        cursor = conn.cursor()
        
        print(f"📝 新しい走行記録を作成します...")
        print(f"   ユーザーID: {user_id}")
        print(f"   動画パス: {video_path}")
        
        # runsテーブルに新規レコードを挿入
        insert_sql = """
            INSERT INTO runs (user_id, video_path, analysis_status, created_at)
            VALUES (%s, %s, 'processing', NOW())
            RETURNING id
        """
        
        cursor.execute(insert_sql, (user_id, video_path))
        run_id = cursor.fetchone()[0]
        
        # 変更を確定
        conn.commit()
        print(f"✅ 走行記録を作成しました: run_id={run_id}")
        
        return str(run_id)
        
    except psycopg2.Error as e:
        print(f"\n❌ データベースエラーが発生しました:")
        print(f"   {str(e)}")
        
        if conn:
            try:
                conn.rollback()
                print("   変更を破棄（rollback）しました")
            except Exception as rollback_error:
                print(f"   ロールバックに失敗: {rollback_error}")
        
        return None
        
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました:")
        print(f"   {type(e).__name__}: {str(e)}")
        
        if conn:
            try:
                conn.rollback()
                print("   変更を破棄（rollback）しました")
            except Exception as rollback_error:
                print(f"   ロールバックに失敗: {rollback_error}")
        
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_run_status(run_id: str, status: str) -> bool:
    """
    走行記録のステータスを更新する関数
    
    Args:
        run_id (str): 走行ID
        status (str): 新しいステータス ('processing', 'completed', 'failed'など)
    
    Returns:
        bool: 更新成功時はTrue、失敗時はFalse
    
    Example:
        >>> success = update_run_status("123", "completed")
        >>> if success:
        >>>     print("ステータスを更新しました")
    """
    conn = None
    cursor = None
    
    try:
        # データベースに接続
        conn = get_db_connection()
        if not conn:
            print("❌ データベース接続に失敗したため、ステータスを更新できません")
            return False
        
        cursor = conn.cursor()
        
        print(f"🔄 走行記録のステータスを更新します...")
        print(f"   run_id: {run_id}")
        print(f"   新しいステータス: {status}")
        
        # runsテーブルのステータスを更新
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
        
        # 変更を確定
        conn.commit()
        print(f"✅ ステータスを'{status}'に更新しました")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ データベースエラーが発生しました:")
        print(f"   {str(e)}")
        
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
        
        if conn:
            try:
                conn.rollback()
                print("   変更を破棄（rollback）しました")
            except Exception as rollback_error:
                print(f"   ロールバックに失敗: {rollback_error}")
        
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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

