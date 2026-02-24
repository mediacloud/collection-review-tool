"""Flask application entry point."""
from flask import Flask, jsonify
from flask_cors import CORS
from config import get_config
from database import init_db, db
from routes.api import api_bp

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
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
