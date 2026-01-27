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
    conn.execute('UPDATE candidates SET status = ? WHERE id = ?', (new_status, candidate_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'status': new_status})

@bp.route('/talent_pool/bulk_delete', methods=['POST'])
@login_required
@role_required('recruiter')
def bulk_delete():
    """AJAX endpoint to delete multiple candidates"""
    data = request.get_json()
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'error': 'No candidates selected'}), 400
    
    try:
        conn = database.get_db_connection()
        placeholders = ','.join('?' for _ in ids)
        conn.execute(f'DELETE FROM candidates WHERE id IN ({placeholders})', ids)
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'deleted': len(ids)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/talent_pool/note/<int:candidate_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def add_note(candidate_id):
    note = request.form.get('note')
    if note is not None:
        database.add_candidate_note(candidate_id, note)
    # Redirect back to the index
    return redirect(url_for('talent_pool.index'))

@bp.route('/talent_pool/udpate/<int:candidate_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def update_candidate(candidate_id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    conn = database.get_db_connection()
    conn.execute('UPDATE candidates SET name = ?, email = ?, phone = ? WHERE id = ?', (name, email, phone, candidate_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('talent_pool.index'))

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
