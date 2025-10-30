-- Migration 003: Create todo_progress_snapshots table
-- Stores AI-generated progress analysis for TODOs

CREATE TABLE IF NOT EXISTS todo_progress_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    todo_id INTEGER NOT NULL,
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_aspects TEXT,  -- JSON array: specific completed items
    remaining_aspects TEXT,  -- JSON array: specific remaining items
    total_time_spent INTEGER,  -- Total minutes spent on TODO
    ai_summary TEXT,  -- AI-generated progress summary
    completion_percentage INTEGER,  -- 0-100
    next_steps TEXT,  -- JSON array: recommended next actions
    FOREIGN KEY (todo_id) REFERENCES user_todos(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_progress_snapshots_todo ON todo_progress_snapshots(todo_id);
CREATE INDEX IF NOT EXISTS idx_progress_snapshots_analyzed_at ON todo_progress_snapshots(analyzed_at DESC);
