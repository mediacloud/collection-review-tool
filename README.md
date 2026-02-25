# MediaCloud Collections Review App

A standalone web application for reviewing sources in MediaCloud collections and exporting decisions as CSV for ingestion by the MediaCloud web-search app.

## Features

- Start or resume reviews for MediaCloud collections
- Review sources one-by-one with Keep/Remove decisions
- Propose new sources to add to collections
- Track review progress with statistics
- Export all decisions as CSV for further processing
- Clean, modern UI built with Svelte

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- MediaCloud API key with read permissions for collections

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Edit `.env` and add your MediaCloud API key:
```
MEDIACLOUD_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///reviews.db
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

## Running the Application

### Development Mode

1. **Start the backend server** (from the `backend` directory):
```bash
python app.py
```

The backend will run on `http://localhost:5000`

2. **Start the frontend development server** (from the `frontend` directory):
```bash
npm run dev
```

The frontend will run on `http://localhost:5173` and proxy API requests to the backend.

3. Open your browser and navigate to `http://localhost:5173`

### Production Build (Local)

1. **Build the frontend**:
```bash
cd frontend
npm run build
```

2. **Serve the built files** (you can use any static file server or configure Flask to serve them):
```bash
npm run preview
```

### Dokku Deployment

This project is designed to deploy to Dokku using helper scripts modeled after MediaCloud's `web-search` app ([`instance.sh`](https://github.com/mediacloud/web-search/blob/main/dokku-scripts/instance.sh), [`push.sh`](https://github.com/mediacloud/web-search/blob/main/dokku-scripts/push.sh)) and the simple Streamlit deploy script from SourceInspector ([`deploy-dokku.sh`](https://github.com/mediacloud/SourceInspector/blob/main/scripts/deploy-dokku.sh)).

#### Overview

- Backend (Flask) and frontend (Svelte) are deployed as a **single Dokku app**.
- Flask serves the built Svelte SPA from `frontend/dist` and exposes the API under `/api/*`.
- Dokku runs the app via a root-level `Procfile` using `gunicorn`.
- Environments are mapped from git branches:
  - `prod` branch → production instance
  - `staging` branch → staging instance
  - any other branch → per-developer instance (based on `$USER`)

#### Key Files

- `Procfile`
  - `web: cd backend && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 3`
  - `release: cd backend && flask --app app:create_app db upgrade`
- `app.json`
  - Runs `npm ci && npm run build` in `frontend/` during Dokku's `predeploy` phase.
- `dokku-scripts/common.sh`
  - Shared config: `APP_BASE`, `DOKKU_GIT_REMOTE`, `FQDN`, `ALLOWED_HOSTS`, `PG_SVC`, etc.
- `dokku-scripts/instance.sh`
  - Creates/destroys Dokku apps and Postgres services for `prod`, `staging`, or a given username.
  - Sets up domains and the Dokku git remote.
- `dokku-scripts/push.sh`
  - Chooses the Dokku instance based on the current git branch.
  - Verifies the branch is pushed to its upstream (unless `--unpushed` is used).
  - Pushes the current branch to the Dokku app's `main` deploy branch.

#### One-Time Setup (per environment)

On a machine with SSH access to the Dokku host:

```bash
cd UNDP_collections_inspector

# Create production instance
dokku-scripts/instance.sh create prod

# Create staging instance
dokku-scripts/instance.sh create staging

# Optionally create a per-user dev instance
dokku-scripts/instance.sh create $USER
```

Then, on the Dokku host, configure any required environment variables, for example:

```bash
dokku config:set undp-collections-review-prod MEDIACLOUD_API_KEY=... SECRET_KEY=...
```

#### Deploying

1. Commit and push your changes to GitHub.
2. Check out the branch you want to deploy:
   - `prod` for production
   - `staging` for staging
   - any other branch for your per-user instance
3. Run:

```bash
./dokku-scripts/push.sh
```

This will:

- Verify the branch is pushed and in sync with its upstream (unless `--unpushed` is used).
- Push the branch to the Dokku remote for the appropriate app.
- Trigger a build that:
  - Installs backend dependencies and runs database migrations (`release` process).
  - Builds the frontend via `app.json`'s `predeploy` script.

## Usage

1. **Start a Review**: Enter a MediaCloud collection ID on the home page and click "Start / Resume Review"
   - If an active review exists for that collection, it will be resumed
   - Otherwise, a new review will be created and sources will be fetched from MediaCloud

2. **Review Sources**: 
   - View each source one at a time
   - Click "Keep" to mark a source to keep
   - Click "Remove" to mark a source for removal
   - The next undecided source will automatically load

3. **Propose New Sources**:
   - Fill in the "Propose New Source" form with a label and homepage URL
   - New sources are automatically marked as "add"

4. **Complete Review**:
   - Click "Complete Review" when finished
   - Review the statistics in the header

5. **Export CSV**:
   - After completion, click "Download CSV Export"
   - The CSV contains all decisions for use in scripts or the main MediaCloud app

## API Endpoints

### Reviews

- `POST /api/reviews/start` - Start or resume a review
  - Body: `{ "collection_id": 123 }`
  - Returns: Review object with stats

- `GET /api/reviews/<review_id>` - Get review details
  - Returns: Review object with stats

- `POST /api/reviews/<review_id>/complete` - Mark review as completed
  - Returns: Updated review object

- `GET /api/reviews/<review_id>/export` - Export review as CSV
  - Returns: CSV file download

### Review Items

- `GET /api/reviews/<review_id>/items` - List review items
  - Query params: `page`, `page_size`, `decision` (filter)
  - Returns: Items array and total count

- `POST /api/reviews/<review_id>/items/<item_id>/decide` - Make a decision
  - Body: `{ "decision": "keep" }` (keep, remove, add, undecided)
  - Returns: Updated item

- `POST /api/reviews/<review_id>/items` - Propose new source
  - Body: `{ "source_label": "Name", "source_homepage": "https://..." }`
  - Returns: Created item

## Database

### Development (SQLite)

The app uses SQLite by default for development. The database file (`reviews.db`) will be created automatically in the backend directory.

### Production (PostgreSQL)

To switch to PostgreSQL, update the `DATABASE_URL` in your `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost/reviews_db
```

Make sure PostgreSQL is installed and the database exists before starting the application.

### Database Migrations

If you need to modify the database schema, you can use Flask-Migrate:

```bash
cd backend
flask db init  # First time only
flask db migrate -m "Description"
flask db upgrade
```

## Environment Variables

- `MEDIACLOUD_API_KEY` (required) - Your MediaCloud API key
- `DATABASE_URL` (optional) - Database connection string (defaults to SQLite)
- `FLASK_DEBUG` (optional) - Enable Flask debug mode (default: False)
- `SECRET_KEY` (optional) - Flask secret key for sessions (change in production)

## Project Structure

```
UNDP_collections_inspector/
├── backend/
│   ├── app.py              # Flask application
│   ├── models.py           # Database models
│   ├── config.py           # Configuration
│   ├── database.py         # Database setup
│   ├── routes/
│   │   └── api.py          # API endpoints
│   └── services/
│       └── mediacloud.py    # MediaCloud API client
├── frontend/
│   ├── src/
│   │   ├── routes/         # Page components
│   │   ├── components/     # Reusable components
│   │   └── lib/
│   │       └── api.js      # API client
│   └── package.json
└── README.md
```

## Troubleshooting

### MediaCloud API Errors

If you encounter errors fetching sources:
- Verify your `MEDIACLOUD_API_KEY` is correct
- Ensure the API key has read permissions for the collection
- Check that the collection ID exists in MediaCloud

### Database Errors

- Ensure the database file/directory is writable (SQLite)
- For PostgreSQL, verify connection credentials and database exists
- Check that all migrations are applied

### Frontend Not Connecting to Backend

- Ensure the backend is running on port 5000
- Check the Vite proxy configuration in `vite.config.js`
- Verify CORS is enabled in the Flask app

## License

This project is for internal use with MediaCloud.

## Support

For issues or questions, please refer to the MediaCloud documentation or contact your system administrator.
