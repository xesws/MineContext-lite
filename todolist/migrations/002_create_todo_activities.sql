-- Migration 002: Create todo_activities table
-- Links screenshots to TODOs based on semantic similarity and manual associations

CREATE TABLE IF NOT EXISTS todo_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    todo_id INTEGER NOT NULL,
    screenshot_id INTEGER NOT NULL,
    activity_description TEXT,
    matched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    match_confidence FLOAT,  -- 0.0-1.0 confidence score
    match_method TEXT,  -- 'semantic', 'keyword', 'manual'
    duration_minutes INTEGER,  -- Estimated activity duration
    activity_type TEXT,  -- 'reading', 'coding', 'video', 'browsing', 'general'
    FOREIGN KEY (todo_id) REFERENCES user_todos(id) ON DELETE CASCADE,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_todo_activities_todo ON todo_activities(todo_id);
CREATE INDEX IF NOT EXISTS idx_todo_activities_screenshot ON todo_activities(screenshot_id);
CREATE INDEX IF NOT EXISTS idx_todo_activities_matched_at ON todo_activities(matched_at DESC);
CREATE INDEX IF NOT EXISTS idx_todo_activities_confidence ON todo_activities(match_confidence DESC);
