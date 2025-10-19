# MineContext-v2

A lightweight, local-first context-aware AI application that automatically captures screenshots, processes them with AI, and provides intelligent insights.

## Current Status

**Phase 1: Core Infrastructure** ✅ COMPLETED
**Phase 2: API Development** ✅ COMPLETED
**Phase 3: Frontend Development** ✅ COMPLETED
**Phase 4: AI Integration** ✅ COMPLETED

- ✅ Project structure initialized
- ✅ Configuration system set up
- ✅ SQLite database layer implemented
- ✅ Screenshot capture service with deduplication
- ✅ Image processing utilities
- ✅ FastAPI server with RESTful API
- ✅ Complete API endpoints for screenshot management
- ✅ Capture control endpoints
- ✅ Static file serving
- ✅ Responsive web UI with Tailwind CSS
- ✅ Gallery and timeline views
- ✅ Interactive lightbox viewer
- ✅ Real-time capture controls and status updates
- ✅ AI-powered screenshot analysis with OpenAI/Anthropic/OpenRouter
- ✅ Automatic description and tag generation
- ✅ Activity categorization
- ✅ Batch analysis functionality

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd tasker_dev
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application (optional)**
   - Copy `.env.example` to `.env` if you plan to use AI features
   - Edit `config/config.yaml` to customize settings

### Running the Application

**Start the server:**

```bash
python run.py
```

The server will start at `http://127.0.0.1:8000` by default.

**Access the application:**
- **Web UI**: `http://127.0.0.1:8000/` (Main application)
- **API Documentation**: `http://127.0.0.1:8000/docs` (Swagger UI)
- **Health Check**: `http://127.0.0.1:8000/health`
- **API Base**: `http://127.0.0.1:8000/api/`

The web interface provides:
- 📸 **Capture Controls** - Start/stop automatic capture or capture manually
- 🖼️ **Gallery View** - Grid layout of all screenshots
- 📅 **Timeline View** - Screenshots organized by date
- 🔍 **Search** - Find screenshots by description, tags, or window title
- 🔎 **Lightbox Viewer** - View, edit, and delete screenshots
- 📊 **Real-time Status** - Live capture status and screenshot count

## Project Structure

```
tasker_dev/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── capture.py           # Screenshot capture service
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite database operations
│   ├── models.py            # Pydantic data models
│   ├── api/
│   │   ├── routes.py        # API endpoint implementations
│   │   └── schemas.py       # Request/response schemas
│   └── utils/
│       └── image_utils.py   # Image processing utilities
├── config/
│   └── config.yaml          # Application configuration
├── screenshots/             # Captured screenshots (auto-created)
├── data/                    # Database storage (auto-created)
├── frontend/                # Web UI (Phase 3)
├── requirements.txt
├── .env.example
├── run.py                   # Server startup script
└── plan.md                  # Detailed implementation plan
```

## Configuration

Edit `config/config.yaml` to customize:

- **Capture settings**: Interval, auto-start, deduplication
- **Storage settings**: Database path, image compression
- **AI settings**: Enable/disable AI features, provider selection
- **Server settings**: Host, port, debug mode

### Enabling AI Features

To use AI-powered screenshot analysis:

1. **Set your API key** in `.env`:
   ```bash
   # For OpenAI
   OPENAI_API_KEY=your-key-here

   # OR for Anthropic Claude
   ANTHROPIC_API_KEY=your-key-here

   # OR for OpenRouter (supports multiple models)
   OPENROUTER_API_KEY=your-key-here
   ```

2. **Enable AI in config.yaml**:
   ```yaml
   ai:
     enabled: true
     provider: openai  # or anthropic, openrouter
     model: gpt-4-vision-preview  # or claude-3-opus-20240229, etc.
     auto_analyze: false
     analyze_on_demand: true
   ```

3. **Restart the server** and use the "Analyze with AI" button in the lightbox or "Analyze Batch (AI)" in the control panel.

**Supported Models:**
- **OpenAI**: `gpt-4-vision-preview`, `gpt-4o`
- **Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- **OpenRouter**: Any vision-capable model (e.g., `google/gemini-pro-vision`, `anthropic/claude-3-opus`, etc.)

## Features (Completed)

### Screenshot Capture
- ✅ Automatic screenshot capture at configurable intervals
- ✅ Perceptual hash-based deduplication
- ✅ Background service with threading
- ✅ Manual capture support
- ✅ Automatic cleanup of old screenshots

### Database
- ✅ SQLite storage for screenshot metadata
- ✅ Full CRUD operations
- ✅ Search functionality
- ✅ Activity tracking support
- ✅ Indexed queries for performance

### Image Processing
- ✅ Perceptual hashing for duplicate detection
- ✅ Image compression with quality control
- ✅ File size optimization
- ✅ Automatic directory management

### RESTful API
- ✅ FastAPI server with automatic OpenAPI documentation
- ✅ Screenshot management endpoints (list, get, update, delete)
- ✅ Capture control endpoints (start, stop, status, manual capture)
- ✅ Timeline view endpoint
- ✅ Search functionality
- ✅ CORS and middleware configuration
- ✅ Static file serving for screenshots and frontend
- ✅ Comprehensive error handling and logging

### Web User Interface
- ✅ Responsive design with Tailwind CSS
- ✅ Gallery view with grid layout and pagination
- ✅ Timeline view grouped by date
- ✅ Interactive lightbox with keyboard navigation (arrow keys, ESC)
- ✅ Capture control panel with real-time status
- ✅ Search and filter interface
- ✅ Edit screenshot descriptions inline
- ✅ Delete screenshots with confirmation
- ✅ Toast notifications for user feedback
- ✅ Auto-refresh when capture is running
- ✅ Mobile-responsive design

### AI Features
- ✅ Multi-provider support (OpenAI, Anthropic, OpenRouter)
- ✅ Vision model integration for screenshot analysis
- ✅ Automatic description generation
- ✅ Smart tag extraction and categorization
- ✅ Activity type classification (coding, browsing, designing, etc.)
- ✅ Single screenshot analysis via lightbox
- ✅ Batch analysis for multiple screenshots
- ✅ Activity tracking in database
- ✅ Configurable on-demand or auto-analysis

## API Endpoints

### Screenshot Management
- `GET /api/screenshots` - List screenshots with pagination
- `GET /api/screenshots/{id}` - Get specific screenshot
- `PATCH /api/screenshots/{id}` - Update screenshot metadata
- `DELETE /api/screenshots/{id}` - Delete screenshot
- `POST /api/screenshots/search` - Search screenshots
- `GET /api/timeline` - Get timeline view

### Capture Control
- `POST /api/capture/start` - Start automatic capture
- `POST /api/capture/stop` - Stop automatic capture
- `GET /api/capture/status` - Get capture service status
- `POST /api/capture/now` - Capture screenshot immediately

### AI Analysis
- `POST /api/screenshots/{id}/analyze` - Analyze single screenshot with AI
- `POST /api/screenshots/analyze-batch` - Batch analyze multiple screenshots

### System
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## Next Steps

See `plan.md` for the complete implementation roadmap:

- ~~**Phase 1**: Core Infrastructure~~ ✅ COMPLETED
- ~~**Phase 2**: API Development~~ ✅ COMPLETED
- ~~**Phase 3**: Frontend Development~~ ✅ COMPLETED
- ~~**Phase 4**: AI Integration~~ ✅ COMPLETED
- **Phase 5**: Polish & Optimization 🚧 NEXT

The application is now **fully functional** with all core features implemented! Phase 5 is optional and focuses on performance improvements and additional polish.

## Development

### Running Tests

Tests will be added in Phase 5.

### Contributing

This is currently a development project. See `plan.md` for planned features.

## License

TBD

## Acknowledgments

Inspired by [MineContext](https://github.com/volcengine/MineContext) by Volcengine.
