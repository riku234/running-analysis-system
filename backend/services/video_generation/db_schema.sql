-- 生成動画テーブル（簡略版 - URLは保存しない、キャッシュで管理）
-- 注意: 現在の実装ではメモリキャッシュを使用しているため、このテーブルは将来の拡張用

CREATE TABLE IF NOT EXISTS generated_videos (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    generation_status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'generating', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_generated_videos_run_id ON generated_videos(run_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_status ON generated_videos(generation_status);

-- コメント追加
COMMENT ON TABLE generated_videos IS '動画生成リクエストの記録用（URLは一時的なためキャッシュで管理）';
COMMENT ON COLUMN generated_videos.prompt_text IS '動画生成に使用したプロンプト';
COMMENT ON COLUMN generated_videos.generation_status IS '生成ステータス: pending, generating, completed, failed';

