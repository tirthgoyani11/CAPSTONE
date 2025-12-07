from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
from flask_login import login_required, current_user

bp = Blueprint('settings', __name__)

@bp.route('/settings')
def index():
    return render_template('settings.html')

@bp.route('/settings/reset', methods=['POST'])
@login_required
def reset_db():
    # 1. Block Candidates
    if current_user.role == 'candidate':
        flash('Unauthorized action.', 'error')
        return redirect(url_for('settings.index'))

    # 2. Recruiter PIN Check
    if current_user.role == 'recruiter':
        pin = request.form.get('pin')
        if pin != '1234': # Hardcoded PIN for now
            # In a real app, this should be in config or env vars
            flash('Invalid PIN. Database wipe aborted.', 'error')
            return redirect(url_for('settings.index'))
            
    # 3. Perform Wipe (Admin or Verified Recruiter)
    if request.form.get('confirm') == 'yes':
        conn = database.get_db_connection()
        conn.execute("DELETE FROM candidates")
        conn.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
        flash('Database cleared successfully.', 'success')
        
    return redirect(url_for('settings.index'))
