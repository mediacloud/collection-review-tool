# MediaCloud Collections Review App - Project Documentation

## Overview

A standalone web application for reviewing sources in MediaCloud collections and exporting decisions as CSV. Built with Flask (backend) and Svelte (frontend).

## Architecture

- **Backend**: Flask + SQLAlchemy (SQLite for dev, PostgreSQL-ready)
- **Frontend**: Svelte SPA with Vite
- **Database**: SQLite (dev) with easy switch to PostgreSQL
- **API Integration**: MediaCloud Python API client (v4)

## Project Structure

```
UNDP_collections_inspector/
├── backend/
│   ├── app.py                 # Flask app entry point
│   ├── models.py              # SQLAlchemy models (Review, ReviewItem)
│   ├── config.py              # Configuration (env vars, database URL)
│   ├── database.py            # Database initialization
│   ├── routes/
│   │   └── api.py             # All API endpoints
│   ├── services/
│   │   └── mediacloud.py     # MediaCloud API client wrapper
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.js            # Svelte app entry
│   │   ├── App.svelte         # Root component with routing
│   │   ├── lib/
│   │   │   └── api.js         # Axios API client
│   │   ├── routes/
│   │   │   ├── Home.svelte    # Start/resume review page
│   │   │   └── Review.svelte  # Review workflow page
│   │   └── components/
│   │       ├── ReviewHeader.svelte    # Stats display
│   │       ├── SourceViewer.svelte    # Current source with Keep/Remove
│   │       └── NewSourceForm.svelte   # Propose new sources
│   ├── package.json
│   └── vite.config.js         # Vite config with proxy to Flask
└── README.md                  # Setup instructions

```

## Key Implementation Details

### Backend

**Database Models:**
- `Review`: Represents a review session for a MediaCloud collection
  - Fields: id, collection_id, status (pending/in_progress/completed), timestamps, name, notes
  - Relationship: one-to-many with ReviewItem
- `ReviewItem`: Represents a source in a review
  - Fields: id, review_id, source_id (nullable), source_label, source_homepage, is_new_source, decision (undecided/keep/remove/add), decided_at

**MediaCloud Integration:**
- Uses `mediacloud.api.DirectoryApi` and `mediacloud.api.SearchApi`
- Import pattern: `import mediacloud.api` then instantiate `DirectoryApi(api_key)`
- Method: `directory.source_list(collection_id=id, limit=100, offset=0)` to fetch sources
- Handles pagination automatically

**API Endpoints:**
- `POST /api/reviews/start` - Start or resume review (creates if new, returns existing if active)
- `GET /api/reviews/<id>` - Get review with stats
- `GET /api/reviews/<id>/items` - List items (supports pagination, decision filter)
- `POST /api/reviews/<id>/items/<item_id>/decide` - Make decision (keep/remove/add)
- `POST /api/reviews/<id>/items` - Propose new source
- `POST /api/reviews/<id>/complete` - Mark review as completed
- `GET /api/reviews/<id>/export` - Download CSV export

### Frontend

**Routing:**
- Simple custom router using browser History API (no external routing library)
- Routes: `/` (Home), `/reviews/:id` (Review)
- Navigation: `window.navigate(path)` function

**State Management:**
- Component-level state (no stores)
- API calls via Axios in `lib/api.js`

**Key Components:**
- `Home.svelte`: Collection ID input, starts/resumes reviews
- `Review.svelte`: Main review workflow, manages current item, handles decisions
- `ReviewHeader.svelte`: Displays collection info and statistics
- `SourceViewer.svelte`: Shows current source with Keep/Remove buttons
- `NewSourceForm.svelte`: Form to propose new sources

## Setup & Running

### Prerequisites
- Python 3.8+ (tested with 3.14)
- Node.js 16+
- MediaCloud API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```
MEDIACLOUD_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///reviews.db
```

Run:
```bash
python app.py
```
Backend runs on `http://localhost:5000`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173` (proxies API to backend)

## Dependencies

### Backend (requirements.txt)
- Flask==3.0.0
- SQLAlchemy>=2.0.36 (2.0.36+ required for Python 3.14 compatibility)
- Flask-CORS==4.0.0
- mediacloud>=4.5.0
- python-dotenv==1.0.0
- Flask-Migrate==4.0.5

### Frontend (package.json)
- svelte: ^4.2.7
- axios: ^1.6.2
- vite: ^5.0.8
- @sveltejs/vite-plugin-svelte: ^3.0.0

**Note**: No routing library - uses custom simple router

## Important Notes

1. **MediaCloud API Client**: 
   - Import: `import mediacloud.api`
   - Use: `mediacloud.api.DirectoryApi(api_key)` and `mediacloud.api.SearchApi(api_key)`
   - No `MediaCloud` class exists - use DirectoryApi/SearchApi directly

2. **Database**: 
   - SQLite for development (auto-created)
   - Switch to PostgreSQL by changing `DATABASE_URL` in `.env`

3. **Review Logic**:
   - Only one active review per collection_id (status != 'completed')
   - New reviews automatically fetch sources from MediaCloud
   - Sources are seeded as ReviewItems with decision='undecided'

4. **CSV Export**:
   - Columns: collection_id, review_id, source_id, source_label, source_homepage, decision, is_new_source
   - Used for ingestion by main MediaCloud web-search app

## Current Features

✅ Start/resume reviews by collection ID
✅ Review sources one-by-one (Keep/Remove decisions)
✅ Propose new sources to add
✅ Track statistics (total, keep, remove, add, undecided)
✅ Complete reviews
✅ Export decisions as CSV
✅ View all decisions in read-only table (completed reviews)

## Known Issues / Future Improvements

- MediaCloud API pagination handling could be more robust
- No user authentication (single-user tool)
- No undo functionality for decisions
- Could add bulk operations for decisions
- Could add filtering/sorting in the review UI

## API Response Examples

**Start Review:**
```json
{
  "review": {
    "id": 1,
    "collection_id": 123,
    "status": "in_progress",
    "stats": {
      "total": 100,
      "keep": 0,
      "remove": 0,
      "add": 0,
      "undecided": 100
    }
  }
}
```

**Review Items:**
```json
{
  "items": [
    {
      "id": 1,
      "source_id": 42,
      "source_label": "Example News",
      "source_homepage": "https://example.com",
      "is_new_source": false,
      "decision": "undecided"
    }
  ],
  "total": 100
}
```

## Development Notes

- Backend uses Flask app factory pattern (`create_app()`)
- CORS enabled for all `/api/*` routes
- Error handling returns JSON with appropriate status codes
- Frontend uses simple reactive state (no stores)
- Routing handles browser back/forward buttons via `popstate` events
