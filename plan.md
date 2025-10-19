# MineContext-v2: Lightweight Context-Aware AI Application

## Project Overview

A lightweight, local-first web application inspired by [MineContext](https://github.com/volcengine/MineContext) that automatically captures screenshots, processes them with AI, and provides intelligent context-aware insights.

## Architecture

### Tech Stack

**Backend:**
- **FastAPI** - Modern Python web framework for building APIs
- **SQLite** - Lightweight relational database for metadata storage
- **Pillow** - Python imaging library for image processing
- **MSS** - Cross-platform screenshot capture library
- **ImageHash** - Perceptual hashing for duplicate detection
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server for FastAPI
- **Loguru** - Enhanced logging

**Frontend:**
- **HTML/CSS/JavaScript** - Simple, lightweight web interface
- **Tailwind CSS** - Utility-first CSS framework
- **Fetch API** - Native HTTP client for API communication

**Optional AI Integration:**
- **OpenAI API** (GPT-4 Vision) - Screenshot analysis and content understanding
- **Anthropic Claude API** - Alternative vision model
- **OpenRouter API** - Unified interface for multiple vision models
- **ChromaDB** - Vector database for semantic search (future enhancement)

### Project Structure

```
tasker_dev/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── capture.py           # Screenshot capture service
│   ├── database.py          # SQLite database operations
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration management
│   ├── api/
│   │   ├── routes.py        # API endpoint definitions
│   │   └── schemas.py       # Request/response schemas
│   └── utils/
│       ├── image_utils.py   # Image processing utilities
│       └── ai_utils.py      # AI/LLM integration utilities
├── frontend/
│   ├── index.html           # Main application UI
│   ├── app.js               # Frontend application logic
│   ├── styles.css           # Custom styles
│   └── components/
│       ├── timeline.js      # Timeline view component
│       └── gallery.js       # Screenshot gallery component
├── screenshots/             # Directory for captured screenshots
├── data/
│   └── context.db           # SQLite database file
├── config/
│   └── config.yaml          # Application configuration
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
└── README.md               # Project documentation
```

## Core Features

### 1. Screenshot Capture Service
- **Automatic Capture**: Captures screenshots at configurable intervals (default: 5 seconds)
- **Smart Deduplication**: Uses perceptual hashing to avoid storing duplicate screenshots
- **Multi-monitor Support**: Handles multiple displays
- **Background Service**: Runs as a background thread/process
- **Pause/Resume**: User control over capture process

### 2. RESTful API
- `GET /api/screenshots` - List all screenshots with metadata
- `GET /api/screenshots/{id}` - Get specific screenshot details
- `POST /api/screenshots/analyze` - Analyze screenshot with AI
- `GET /api/timeline` - Get timeline view of activities
- `POST /api/capture/start` - Start screenshot capture
- `POST /api/capture/stop` - Stop screenshot capture
- `GET /api/capture/status` - Get capture service status
- `GET /api/search` - Search screenshots by description/tags
- `DELETE /api/screenshots/{id}` - Delete screenshot

### 3. SQLite Database Schema
```sql
screenshots (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_hash TEXT,
    description TEXT,
    tags TEXT,
    app_name TEXT,
    window_title TEXT,
    analyzed BOOLEAN DEFAULT 0,
    file_size INTEGER
)

activities (
    id INTEGER PRIMARY KEY,
    screenshot_id INTEGER,
    activity_type TEXT,
    content TEXT,
    timestamp DATETIME,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id)
)
```

### 4. Web User Interface
- **Timeline View**: Chronological display of captured screenshots
- **Gallery View**: Grid layout for browsing
- **Search Interface**: Filter by date, description, tags
- **Screenshot Viewer**: Lightbox for detailed viewing
- **Control Panel**: Start/stop capture, configure settings
- **Activity Dashboard**: View summaries and insights

### 5. AI-Powered Analysis (Optional)
- **Visual Understanding**: Describe screenshot content using Vision LLMs
- **Entity Extraction**: Identify text, UI elements, applications
- **Activity Recognition**: Categorize user activities (coding, browsing, designing)
- **Smart Tagging**: Automatic tag generation
- **Contextual Summaries**: Generate daily/weekly activity reports

## Implementation Steps

### ~~Phase 1: Core Infrastructure~~ ✅
~~1. **Project Setup**~~
   ~~- Initialize directory structure~~
   ~~- Create virtual environment~~
   ~~- Install dependencies~~
   ~~- Set up configuration system~~

~~2. **Database Layer**~~
   ~~- Define SQLite schema~~
   ~~- Create database initialization script~~
   ~~- Implement CRUD operations~~
   ~~- Add migration support~~

~~3. **Screenshot Capture**~~
   ~~- Implement MSS-based screenshot capture~~
   ~~- Add perceptual hashing for deduplication~~
   ~~- Create background service with threading~~
   ~~- Add file management and cleanup~~

### ~~Phase 2: API Development~~ ✅
~~4. **FastAPI Server**~~
   ~~- Set up FastAPI application~~
   ~~- Configure CORS and middleware~~
   ~~- Implement health check endpoints~~
   ~~- Add logging and error handling~~

~~5. **API Endpoints**~~
   ~~- Screenshot management endpoints~~
   ~~- Capture control endpoints~~
   ~~- Timeline and activity endpoints~~
   ~~- Search functionality~~

~~6. **Static File Serving**~~
   ~~- Configure FastAPI to serve frontend~~
   ~~- Set up screenshot file access~~
   ~~- Add proper MIME types~~

### ~~Phase 3: Frontend Development~~ ✅
~~7. **Basic UI Structure**~~
   ~~- Create HTML layout~~
   ~~- Implement responsive design with Tailwind~~
   ~~- Add navigation and routing~~

~~8. **Screenshot Display**~~
   ~~- Build timeline component~~
   ~~- Create gallery grid view~~
   ~~- Implement image viewer/lightbox~~
   ~~- Add pagination~~

~~9. **Interactive Controls**~~
   ~~- Capture start/stop buttons~~
   ~~- Settings panel~~
   ~~- Search and filter interface~~
   ~~- Real-time status updates~~

### ~~Phase 4: AI Integration (Optional)~~ ✅
~~10. **LLM Integration**~~
    ~~- Set up OpenAI/Claude/OpenRouter API client~~
    ~~- Implement vision model calls~~
    ~~- Add prompt engineering for analysis~~
    ~~- Cache AI responses~~

~~11. **Smart Features**~~
    ~~- Automatic screenshot description~~
    ~~- Activity categorization~~
    ~~- Tag generation~~
    ~~- Summary generation~~

### Phase 5: Polish & Optimization
12. **Performance Optimization**
    - Image compression
    - Database indexing
    - Lazy loading in UI
    - Background task optimization

13. **Testing & Documentation**
    - Unit tests for core functions
    - API endpoint tests
    - User documentation
    - Configuration guide

## Key Libraries & Dependencies

### Python Backend
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0
pillow>=10.0.0
mss>=9.0.0
imagehash>=4.3.0
loguru>=0.7.0
python-multipart>=0.0.6
aiofiles>=23.2.0
pyyaml>=6.0.0
python-dotenv>=1.0.0

# Optional AI Integration
openai>=1.3.0  # Also compatible with OpenRouter API
anthropic>=0.7.0
chromadb>=0.4.0  # For future vector search
```

### Frontend
```
- Tailwind CSS (via CDN or build process)
- Native JavaScript (ES6+)
- No heavy framework dependencies
```

## AI Models & APIs

### Vision Models (Choose One)
1. **OpenAI GPT-4 Vision**
   - API: `gpt-4-vision-preview`
   - Best for: Detailed screenshot analysis
   - Cost: ~$0.01-0.03 per image

2. **Anthropic Claude 3**
   - API: `claude-3-opus` or `claude-3-sonnet`
   - Best for: Context understanding, privacy-conscious users
   - Cost: Varies by model tier

3. **OpenRouter**
   - API: Multiple models via unified interface (GPT-4V, Claude 3, Gemini Pro Vision, etc.)
   - Best for: Flexibility, model comparison, cost optimization
   - Cost: Varies by model, competitive pricing
   - Endpoint: `https://openrouter.ai/api/v1`

### Embedding Models (Optional, for semantic search)
- OpenAI: `text-embedding-3-small`
- Open source: `sentence-transformers`

## Configuration Options

### config.yaml
```yaml
capture:
  interval_seconds: 5
  auto_start: false
  screenshot_dir: ./screenshots
  max_screenshots: 10000
  deduplicate: true
  hash_threshold: 5

storage:
  database_path: ./data/context.db
  compression: true
  quality: 85

ai:
  enabled: false
  provider: openai  # or anthropic, openrouter
  model: gpt-4-vision-preview
  auto_analyze: false
  analyze_on_demand: true

server:
  host: 127.0.0.1
  port: 8000
  debug: false
```

## Privacy & Security Considerations

1. **Local-First**: All data stored locally by default
2. **API Key Security**: Environment variables for sensitive credentials
3. **No Telemetry**: No data sent to external services without explicit user consent
4. **Selective Analysis**: Users choose which screenshots to analyze with AI
5. **Data Cleanup**: Configurable retention policies

## Future Enhancements

1. **Vector Search**: Add ChromaDB for semantic screenshot search
2. **Desktop App**: Electron wrapper for native system tray integration
3. **OCR Integration**: Extract text from screenshots (Tesseract)
4. **Multi-Source Context**: Browser history, clipboard, file changes
5. **Smart Notifications**: Proactive insights and reminders
6. **Export/Backup**: Data export to various formats
7. **Plugin System**: Extensible architecture for custom processors

## Success Metrics

- ✅ Capture screenshots reliably without performance impact
- ✅ Web UI loads in <2 seconds
- ✅ API response time <200ms for most endpoints
- ✅ Deduplicate >90% of redundant screenshots
- ✅ AI analysis (optional) provides useful descriptions
- ✅ Local storage management keeps disk usage reasonable
