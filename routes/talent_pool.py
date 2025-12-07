from flask import Blueprint, render_template, request
import database

bp = Blueprint('talent_pool', __name__)

from flask_login import login_required
from decorators import role_required

@bp.route('/talent_pool')
@login_required
@role_required('recruiter')
def index():
    query = request.args.get('q', '')
    conn = database.get_db_connection()
    
    if query:
        # Simple SQL LIKE search
        candidates = conn.execute(
            "SELECT * FROM candidates WHERE filename LIKE ? OR full_text LIKE ? ORDER BY created_at DESC", 
            (f'%{query}%', f'%{query}%')
        ).fetchall()
    else:
        candidates = conn.execute('SELECT * FROM candidates ORDER BY created_at DESC').fetchall()
        
    conn.close()
    return render_template('talent_pool.html', candidates=candidates, query=query)
