from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import database
from decorators import role_required
from datetime import datetime

bp = Blueprint('interviews', __name__)

@bp.route('/interviews')
@login_required
@role_required('recruiter')
def index():
    conn = database.get_db_connection()
    # Fetch interviews with candidate name and job title
    query = '''
        SELECT i.*, c.name as candidate_name, c.filename as candidate_filename, j.title as job_title, u.name as interviewer_name
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        LEFT JOIN jobs j ON c.job_id = j.id
        LEFT JOIN users u ON i.interviewer_id = u.id
        ORDER BY i.start_time ASC
    '''
    rows = conn.execute(query).fetchall()
    
    # Process rows to convert string timestamps to datetime objects (SQLite specific fix)
    interviews = []
    for row in rows:
        interview = dict(row)
        if isinstance(interview['start_time'], str):
            try:
                # SQLite often stores as 'YYYY-MM-DD HH:MM:SS' or with microseconds
                interview['start_time'] = datetime.strptime(interview['start_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    interview['start_time'] = datetime.strptime(interview['start_time'], '%Y-%m-%d %H:%M:%S.%f')
                except:
                    pass # Keep as string or handle error
        interviews.append(interview)

    # Also fetch candidates for the "Schedule New" modal dropdown
    candidates = conn.execute('SELECT id, name, filename FROM candidates ORDER BY name').fetchall()
    conn.close()
    
    return render_template('interviews.html', interviews=interviews, candidates=candidates)

@bp.route('/interviews/schedule', methods=['POST'])
@login_required
@role_required('recruiter')
def schedule():
    candidate_id = request.form.get('candidate_id')
    start_time_str = request.form.get('start_time')
    location = request.form.get('location')
    notes = request.form.get('notes')
    
    if not candidate_id or not start_time_str:
        flash('Candidate and Start Time are required.', 'error')
        return redirect(url_for('interviews.index'))

    try:
        # Parse datetime-local input (format: YYYY-MM-DDTHH:MM)
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        # Default duration 1 hour
        end_time = datetime.fromtimestamp(start_time.timestamp() + 3600)
        
        conn = database.get_db_connection()
        conn.execute('''
            INSERT INTO interviews (candidate_id, interviewer_id, start_time, end_time, location, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (candidate_id, current_user.id, start_time, end_time, location, notes))
        
        # Log activity
        conn.execute('''
            INSERT INTO activity_logs (candidate_id, user_id, action_type, description)
            VALUES (?, ?, 'interview', ?)
        ''', (candidate_id, current_user.id, f"Scheduled interview for {start_time.strftime('%b %d, %H:%M')}"))
        
        conn.commit()
        conn.close()
        
        flash('Interview scheduled successfully.', 'success')
        
    except ValueError:
        flash('Invalid date format.', 'error')
    except Exception as e:
        print(f"Error scheduling interview: {e}")
        flash('Failed to schedule interview.', 'error')
        
    return redirect(url_for('interviews.index'))

@bp.route('/interviews/delete/<int:id>', methods=['POST'])
@login_required
@role_required('recruiter')
def delete(id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM interviews WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Interview cancelled.', 'info')
    return redirect(url_for('interviews.index'))
