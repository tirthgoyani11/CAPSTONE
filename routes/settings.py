from flask import Blueprint, render_template, request, redirect, url_for, flash
import database

bp = Blueprint('settings', __name__)

@bp.route('/settings')
def index():
    return render_template('settings.html')

@bp.route('/settings/reset', methods=['POST'])
def reset_db():
    if request.form.get('confirm') == 'yes':
        conn = database.get_db_connection()
        conn.execute("DELETE FROM candidates")
        conn.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
    return redirect(url_for('settings.index'))
