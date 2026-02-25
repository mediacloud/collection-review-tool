"""Flask application entry point."""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import get_config
from database import init_db, db
from routes.api import api_bp

def create_app():
    """Create and configure Flask application."""

    # Configure static and template folders to serve built frontend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dist = os.path.abspath(os.path.join(backend_dir, "..", "frontend", "dist"))

    app = Flask(
        __name__,
        static_folder=frontend_dist,
        template_folder=frontend_dist,
    )
    config = get_config()
    
    # Load configuration
    app.config.from_object(config)
    
    # Initialize database
    init_db(app)
    
    # Enable CORS for frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'ok'}), 200

    # Catch-all route to serve the Svelte SPA and its static assets for non-API paths
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def spa(path):
        """
        Serve the frontend SPA (and built assets) for any non-API route.

        Dokku deployment will serve the built Svelte app from frontend/dist.
        """
        # Let API and health routes be handled by their own view functions
        if path.startswith('api/') or path == 'health':
            return jsonify({'error': 'Not found'}), 404

        # If a built asset exists at this path (e.g. /assets/*.js, /assets/*.css),
        # serve it directly instead of returning index.html.
        asset_fs_path = os.path.join(frontend_dist, path)
        if path and os.path.isfile(asset_fs_path):
            return send_from_directory(frontend_dist, path)

        index_path = os.path.join(frontend_dist, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dist, 'index.html')
        # If the frontend hasn't been built yet, return a helpful error
        return jsonify({'error': 'Frontend build not found'}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
