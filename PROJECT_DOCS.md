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
│   │   │   ├── Home.svelte            # ReviewProject creation + ReviewProjects landing table
│   │   │   ├── ReviewProject.svelte  # Manager view (Step 2 queue generation + export)
│   │   │   └── Review.svelte         # Reviewer queue workflow (queue_guid)
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
- `ReviewProject`: Manager-level container for a multi-collection review project
  - Stores seed `collection_ids` and seed collection names
  - Step 1 stores deduped seed sources at the project level
  - Status is computed on read from its reviewer queues (derived/computed, not manually set)
- `ReviewProjectSource`: Deduped seed source belonging to a `ReviewProject`
  - Stores `source_id` and the MediaCloud metadata needed for later CSV export
- `Review`: Used as a reviewer queue when linked to a `ReviewProject`
  - Has `queue_guid` + `queue_index` and belongs to `review_project_id`
  - Queue completion is derived from whether undecided `ReviewItem`s remain
- `ReviewItem`: A source row inside a reviewer queue
  - Stores decisions (undecided/keep/remove/add) and the full `source_metadata` payload

**MediaCloud Integration:**
- Uses `mediacloud.api.DirectoryApi` and `mediacloud.api.SearchApi`
- Import pattern: `import mediacloud.api` then instantiate `DirectoryApi(api_key)`
- Method: `directory.source_list(collection_id=id, limit=100, offset=0)` to fetch sources
- Handles pagination automatically

**API Endpoints:**
- `POST /api/review-projects/start` - Step 1: create ReviewProject + store deduped sources
- `POST /api/review-projects/<project_guid>/queues` - Step 2: generate reviewer queues from project sources
- `PATCH /api/review-projects/<project_guid>/edit-metadata` - Project-level metadata toggle (propagates to reviewer queues)
- `PATCH /api/review-projects/<project_guid>/name` - Update a ReviewProject's display name
- `GET /api/review-projects` - List projects with derived status + aggregated queue stats
- `GET /api/review-projects/<project_guid>` - Project details + per-queue summaries (derived on read)
- `GET /api/review-projects/<project_guid>/export` - Export a single aggregated project CSV (KEEP + ADD union)
- `GET /api/review-projects/<project_guid>/skipped-items` - Virtual queue endpoint for `decision=skip`
- `GET /api/review-projects/<project_guid>/added-items` - Virtual queue endpoint for `decision=add`
- `GET /api/review-projects/<project_guid>/removed-items` - Virtual queue endpoint for `decision=remove`
- `GET /api/review-queues/<queue_guid>` - Get a reviewer queue (status is derived when exhausted)
- `GET /api/review-queues/<queue_guid>/guidelines` - Rendered guidelines for the queue
- `GET /api/review-queues/<queue_guid>/items` - List queue items (supports pagination + decision filter)
- `POST /api/review-queues/<queue_guid>/items/<item_id>/decide` - Make a decision in the queue
- `POST /api/review-queues/<queue_guid>/items` - Propose a new source in the queue

### Frontend

**Routing:**
- Simple custom router using browser History API (no external routing library)
- Routes:
  - `/` (Home)
  - `/review-projects/:guid` (ReviewProject manager view)
  - `/reviews/:queue_guid` (Reviewer Queue)
  - `/review-projects/:guid/skipped` (Virtual skipped sources)
  - `/review-projects/:guid/added` (Virtual added sources)
  - `/review-projects/:guid/removed` (Virtual removed sources)
- Navigation: `window.navigate(path)` function

**State Management:**
- Component-level state (no stores)
- API calls via Axios in `lib/api.js`

**Key Components:**
- `Home.svelte`: ReviewProject creation form + ReviewProjects landing table
- `ReviewProject.svelte`: Manager view for a project (generate reviewer queues + project CSV export)
- `Review.svelte`: Reviewer queue workflow (GUID-based), handles item decisions + proposing new sources
- `ReviewSkippedQueue.svelte`: Virtual queue page for skipped sources
- `ReviewAddedQueue.svelte`: Virtual queue page for added sources
- `ReviewRemovedQueue.svelte`: Virtual queue page for removed sources (includes requeue action)
- `SourceViewer.svelte`: Shows current source with Keep/Remove buttons
- `NewSourceModal.svelte`: Modal form to propose new sources (with optional metadata fields)
- `EditMetadataModal.svelte`: Modal to edit per-source metadata in queues
- `RemovalReasonModal.svelte`: Modal to capture removal reason

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

## Dokku Deployment

The app includes Dokku deployment scripts modeled after the MediaCloud `web-search` project ([`instance.sh`](https://github.com/mediacloud/web-search/blob/main/dokku-scripts/instance.sh), [`push.sh`](https://github.com/mediacloud/web-search/blob/main/dokku-scripts/push.sh)) and the `deploy-dokku.sh` script from SourceInspector ([link](https://github.com/mediacloud/SourceInspector/blob/main/scripts/deploy-dokku.sh)).

### Runtime Model

- Single Dokku app per environment (prod, staging, per-developer).
- Flask serves both:
  - API under `/api/*`
  - Built Svelte SPA from `frontend/dist` for all other routes.
- Dokku process types (from `Procfile`):
  - `web`: `cd backend && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 3`
  - `release`: `cd backend && flask --app app:create_app db upgrade`
- Frontend build is run via `app.json`:
  - `scripts.dokku.predeploy`: `cd frontend && npm ci && npm run build`

### Environments

- `prod` git branch → `INSTANCE=prod` → Dokku app `undp-collections-review-prod`
- `staging` git branch → `INSTANCE=staging` → Dokku app `undp-collections-review-staging`
- any other git branch → `INSTANCE=$USER` → Dokku app `undp-collections-review-$USER`

Domains (`ALLOWED_HOSTS`) are derived from `INSTANCE` in `dokku-scripts/common.sh` and applied via `dokku domains:add`.

### Scripts

- `dokku-scripts/common.sh`
  - Computes `APP`, `PG_SVC`, `ALLOWED_HOSTS` from `INSTANCE`.
  - Defines `APP_BASE`, `DOKKU_GIT_REMOTE`, and `FQDN` (Dokku SSH host).
  - Provides `check_not_root` helper.

- `dokku-scripts/instance.sh`
  - Usage: `instance.sh create|destroy prod|staging|USERNAME`
  - On `create`:
    - Ensures Dokku app `$APP` exists.
    - Ensures postgres service `$PG_SVC` exists and is linked to `$APP`.
    - Configures domains based on `ALLOWED_HOSTS`.
    - Ensures the local git remote `$DOKKU_GIT_REMOTE` points at `dokku@$FQDN:$APP`.
  - On `destroy`:
    - Destroys the Dokku app and the associated postgres service.

- `dokku-scripts/push.sh`
  - Determines `INSTANCE` from the current git branch:
    - `prod` / `staging` → same-named instance.
    - anything else → `$USER`.
  - Sources `common.sh` to compute `APP` and related settings.
  - Verifies the current branch is pushed and in sync with its upstream (unless `--unpushed` is used).
  - Sets Dokku deploy branch for the app to `main` and pushes the current branch to `main` on the Dokku remote.

### Typical Workflow

1. One-time per environment:
   - `dokku-scripts/instance.sh create prod`
   - `dokku-scripts/instance.sh create staging`
   - `dokku-scripts/instance.sh create $USER` (optional per-dev instance)
2. On the Dokku host, set required env vars for each app (`MEDIACLOUD_API_KEY`, `SECRET_KEY`, etc.).
3. For each deploy:
   - Check out the target branch (`prod`, `staging`, or your feature branch).
   - Ensure it is pushed to GitHub.
   - Run `./dokku-scripts/push.sh`.

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
  - Step 1 creates a `ReviewProject` from multiple seed `collection_id`s and stores deduped sources at the project level (`ReviewProjectSource`)
  - Step 2 generates reviewer queues by partitioning the project's deduped sources into disjoint buckets (`queue_count`)
  - Queue and project statuses are derived on read: a queue is “completed” when it is exhausted (no undecided items remain)
  - Project CSV export aggregates the union of **KEEP + ADD** decisions across all queues

4. **CSV Export**:
  - Project export is a single aggregated CSV across all reviewer queues
  - Includes the union of **KEEP + ADD** decisions (while REMOVE decisions are not exported)
  - CSV columns follow the existing MediaCloud mapping defined by `mc_csv_columns.txt`

## Current Features

✅ Start ReviewProjects from multiple collections (deduped sources)
✅ Two-step workflow (Step 1 seed + Step 2 generate reviewer queues)
✅ Queue progress + derived completion when exhausted
✅ Persistent reviewer decisions (KEEP/REMOVE/ADD) and proposed new sources
✅ Virtual queue pages for skipped/added/removed sources (with empty-state messaging)
✅ Project-level editing controls:
  - editable project display name
  - toggle for “Edit source metadata in queues” (propagates to reviewer queues)
✅ Reviewer URL copy-to-clipboard (full URL) for sharing queues
✅ Project-level aggregated CSV export (KEEP + ADD union across queues)

## Known Issues / Future Improvements

- MediaCloud API pagination handling could be more robust
- No user authentication (single-user tool)
- No undo functionality for decisions
- Could add bulk operations for decisions
- Could add filtering/sorting in the review UI

## API Response Examples

**Start ReviewProject (Step 1):**
```json
{
  "project": {
    "guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "collection_ids": [123, 456],
    "collection_names": ["Collection 123", "Collection 456"],
    "name": "ReviewProject (2 collections)"
  },
  "derived_status": "pending",
  "queues": [],
  "stats": { "total": 100, "keep": 0, "remove": 0, "add": 0, "undecided": 100, "skip": 0 }
}
```

**ReviewQueue Items:**
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
