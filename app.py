import os
from flask import Flask, redirect, url_for
import database
from routes import talent_pool, analytics, settings, core

# Initialize App and DB
app = Flask(__name__)
# Config
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-prod' # Required for session
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Custom Jinja2 Filters
import json

@app.template_filter('from_json')
def from_json_filter(value):
    """Parse a JSON string into a Python object."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

database.init_db()

# Initialize Authentication
from flask_login import LoginManager
from database import User

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Register Blueprints
from routes import auth # New Auth Route
app.register_blueprint(auth.bp)
app.register_blueprint(core.bp)
app.register_blueprint(talent_pool.bp)
app.register_blueprint(analytics.bp)
app.register_blueprint(settings.bp)

from routes import export_routes
app.register_blueprint(export_routes.bp)

from routes import interviews
app.register_blueprint(interviews.bp)

# Global error handlers or context processors can go here

if __name__ == '__main__':
    app.run(debug=True)
