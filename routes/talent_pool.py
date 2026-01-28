from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import database

bp = Blueprint('talent_pool', __name__)

from flask_login import login_required
from decorators import role_required

# Pipeline statuses in order
PIPELINE_STATUSES = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired', 'Rejected']

@bp.route('/talent_pool')
@login_required
@role_required('recruiter')
def index():
    query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    conn = database.get_db_connection()
    
    # Build dynamic query with filters
    base_query = '''
        SELECT c.*, j.title as job_role
        FROM candidates c
        LEFT JOIN jobs j ON c.job_id = j.id
        WHERE 1=1
    '''
    params = []
    
    if query:
        base_query += ' AND (c.filename LIKE ? OR c.full_text LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    
    if status_filter:
        base_query += ' AND c.status = ?'
        params.append(status_filter)
    
    # Sorting
    valid_sorts = ['created_at', 'total_score', 'filename', 'status']
    if sort_by not in valid_sorts:
        sort_by = 'created_at'
    order = 'DESC' if sort_order == 'desc' else 'ASC'
    base_query += f' ORDER BY c.{sort_by} {order}'
    
    candidates = conn.execute(base_query, params).fetchall()
    
    # Pipeline statistics
    pipeline_stats = {}
    for status in PIPELINE_STATUSES:
        count = conn.execute('SELECT COUNT(*) FROM candidates WHERE status = ?', (status,)).fetchone()[0]
        pipeline_stats[status] = count
    
    conn.close()
    return render_template('talent_pool.html', 
                         candidates=candidates, 
                         query=query,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         pipeline_stats=pipeline_stats,
                         statuses=PIPELINE_STATUSES)

@bp.route('/talent_pool/activity/<int:candidate_id>')
@login_required
@role_required('recruiter')
def get_activity_log(candidate_id):
    """AJAX endpoint to getting activity log"""
    conn = database.get_db_connection()
    logs = conn.execute('''
        SELECT a.*, u.name as user_name 
        FROM activity_logs a 
        LEFT JOIN users u ON a.user_id = u.id 
        WHERE a.candidate_id = ? 
        ORDER BY a.created_at DESC
    ''', (candidate_id,)).fetchall()
    conn.close()
    
    log_list = []
    for log in logs:
        log_list.append({
            'user_name': log['user_name'] or 'System',
            'action_type': log['action_type'],
            'description': log['description'],
            'created_at': log['created_at']
        })
        
    return jsonify(log_list)

@bp.route('/talent_pool/status/<int:candidate_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def update_status(candidate_id):
    """AJAX endpoint to update candidate pipeline status"""
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in PIPELINE_STATUSES:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = database.get_db_connection()
    # Get old status
    old_status = conn.execute("SELECT status FROM candidates WHERE id = ?", (candidate_id,)).fetchone()[0]
    
    if old_status != new_status:
        conn.execute('UPDATE candidates SET status = ? WHERE id = ?', (new_status, candidate_id))
        # Log activity
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = None # or system user

        conn.execute('''
            INSERT INTO activity_logs (candidate_id, user_id, action_type, description) 
            VALUES (?, ?, 'status_change', ?)
        ''', (candidate_id, user_id, f"Changed status from {old_status} to {new_status}"))
        
        # Send Email Notification
        cand_info = conn.execute('''
            SELECT c.name, c.email, j.title as job_title 
            FROM candidates c 
            LEFT JOIN jobs j ON c.job_id = j.id 
            WHERE c.id = ?
        ''', (candidate_id,)).fetchone()
        
        if cand_info and cand_info['email']:
            from utils.email_service import EmailService
            EmailService.send_status_update(
                cand_info['name'], 
                cand_info['email'], 
                new_status, 
                cand_info['job_title'],
                candidate_id=candidate_id,
                base_url=request.host_url
            )

        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'status': new_status})

@bp.route('/talent_pool/note/<int:candidate_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def add_note(candidate_id):
    note = request.form.get('note')
    if note:
        conn = database.get_db_connection()
        # Add to notes column AND activity log
        conn.execute('UPDATE candidates SET notes = ? WHERE id = ?', (note, candidate_id))
        conn.execute('''
            INSERT INTO activity_logs (candidate_id, user_id, action_type, description) 
            VALUES (?, ?, 'note', ?)
        ''', (candidate_id, current_user.id, note))
        conn.commit()
        conn.close()
        
    return redirect(url_for('talent_pool.index'))

@bp.route('/talent_pool/update/<int:candidate_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def update_candidate(candidate_id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    conn = database.get_db_connection()
    # Get job_id for redirect
    job_id = conn.execute('SELECT job_id FROM candidates WHERE id = ?', (candidate_id,)).fetchone()[0]
    
    conn.execute('UPDATE candidates SET name = ?, email = ?, phone = ? WHERE id = ?', (name, email, phone, candidate_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('core.job_detail', job_id=job_id))

@bp.route('/compare')
@login_required
@role_required('recruiter')
def compare():
    candidate_ids = request.args.getlist('ids')
    if not candidate_ids:
        return redirect(url_for('talent_pool.index'))
    
    # Convert string IDs to integers
    try:
        candidate_ids = [int(id) for id in candidate_ids]
    except ValueError:
        return redirect(url_for('talent_pool.index'))
    
    # Securely query for multiple IDs
    # Using parameterized query with dynamic placeholders
    placeholders = ','.join('?' for _ in candidate_ids)
    query = f"SELECT * FROM candidates WHERE id IN ({placeholders})"
    
    conn = database.get_db_connection()
    candidates = conn.execute(query, candidate_ids).fetchall()
    conn.close()
    
    return render_template('compare.html', candidates=candidates)
