-- ============================================================================
-- Running Analysis System - Database Schema
-- ============================================================================

-- 1. ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 走行記録テーブル（メインテーブル）
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    video_id VARCHAR(255) UNIQUE NOT NULL,
    video_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    video_fps FLOAT,
    video_duration FLOAT,
    total_frames INTEGER,
    analysis_status VARCHAR(50) DEFAULT 'processing',
    -- 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. キーポイントデータテーブル（時系列座標）
CREATE TABLE IF NOT EXISTS keypoints (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    landmark_id INTEGER NOT NULL,
    landmark_name VARCHAR(100),
    x_coordinate FLOAT NOT NULL,
    y_coordinate FLOAT NOT NULL,
    z_coordinate FLOAT,
    visibility FLOAT,
    body_part VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
    UNIQUE (run_id, frame_number, landmark_id)
);

-- 4. 解析結果テーブル（計算結果）
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value NUMERIC NOT NULL,
    unit VARCHAR(50),
    category VARCHAR(100),
    -- 'basic', 'z_score', 'event', 'angle'など
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
    UNIQUE (run_id, metric_name)
);

-- 5. イベント検出テーブル（足接地・離地）
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    -- 'left_strike', 'left_off', 'right_strike', 'right_off'
    foot_side VARCHAR(10) NOT NULL,
    -- 'left', 'right'
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- 6. アドバイステーブル
CREATE TABLE IF NOT EXISTS advice (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    advice_text TEXT NOT NULL,
    advice_type VARCHAR(100),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- 7. 角度時系列データテーブル（各フレームの関節角度）
CREATE TABLE IF NOT EXISTS frame_angles (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    timestamp FLOAT,
    trunk_angle FLOAT,
    left_thigh_angle FLOAT,
    right_thigh_angle FLOAT,
    left_lower_leg_angle FLOAT,
    right_lower_leg_angle FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
    UNIQUE (run_id, frame_number)
);

-- 8. 診断ルールテーブル（ルールベース診断用）
CREATE TABLE IF NOT EXISTS diagnosis_rules (
    id SERIAL PRIMARY KEY,
    rule_code VARCHAR(100) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    target_event VARCHAR(50),
    -- 'right_strike', 'right_off', 'left_strike', 'left_off', NULL (全イベント)
    target_metric VARCHAR(100) NOT NULL,
    -- '体幹角度', '左大腿角度', '右大腿角度', '左下腿角度', '右下腿角度'
    operator VARCHAR(10) NOT NULL,
    -- 'lt', 'gt', 'lte', 'gte', 'eq'
    threshold FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    -- 'high', 'medium', 'low'
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 9. 専門家アドバイステーブル（ルールベース診断用）
CREATE TABLE IF NOT EXISTS expert_advice (
    id SERIAL PRIMARY KEY,
    rule_code VARCHAR(100) NOT NULL,
    issue_name VARCHAR(255) NOT NULL,
    observation TEXT,
    cause TEXT,
    action TEXT,
    drill_name VARCHAR(255),
    drill_url VARCHAR(500),
    additional_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (rule_code) REFERENCES diagnosis_rules(rule_code) ON DELETE CASCADE
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_video_id ON runs(video_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(analysis_status);
CREATE INDEX IF NOT EXISTS idx_keypoints_run_id ON keypoints(run_id);
CREATE INDEX IF NOT EXISTS idx_keypoints_frame ON keypoints(run_id, frame_number);
CREATE INDEX IF NOT EXISTS idx_analysis_results_run_id ON analysis_results(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_advice_run_id ON advice(run_id);
CREATE INDEX IF NOT EXISTS idx_frame_angles_run_id ON frame_angles(run_id);
CREATE INDEX IF NOT EXISTS idx_frame_angles_frame ON frame_angles(run_id, frame_number);
CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_code ON diagnosis_rules(rule_code);
CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_metric ON diagnosis_rules(target_metric);
CREATE INDEX IF NOT EXISTS idx_diagnosis_rules_event ON diagnosis_rules(target_event);
CREATE INDEX IF NOT EXISTS idx_expert_advice_rule_code ON expert_advice(rule_code);

