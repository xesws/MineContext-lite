-- Migration 001: Create user_todos table
-- User-defined TODO items with hierarchical support (parent-child relationships)

CREATE TABLE IF NOT EXISTS user_todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    parent_id INTEGER,  -- For subtasks, references parent TODO
    status TEXT DEFAULT 'pending',  -- pending/in_progress/completed/archived
    priority TEXT DEFAULT 'medium',  -- low/medium/high
    tags TEXT,  -- Comma-separated tags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    estimated_hours FLOAT,
    completion_percentage INTEGER DEFAULT 0,
    embedding BLOB,  -- Serialized numpy array for semantic matching
    FOREIGN KEY (parent_id) REFERENCES user_todos(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_todos_status ON user_todos(status);
CREATE INDEX IF NOT EXISTS idx_user_todos_parent ON user_todos(parent_id);
CREATE INDEX IF NOT EXISTS idx_user_todos_due_date ON user_todos(due_date);
CREATE INDEX IF NOT EXISTS idx_user_todos_created_at ON user_todos(created_at DESC);
