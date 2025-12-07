from flask import Blueprint, render_template
import database

bp = Blueprint('analytics', __name__)

from flask_login import login_required
from decorators import role_required

@bp.route('/analytics')
@login_required
@role_required('recruiter')
def index():
    conn = database.get_db_connection()
    
    # 1. Candidates per Job
    jobs = conn.execute("SELECT id, title FROM jobs").fetchall()
    job_labels = []
    job_counts = []
    
    for job in jobs:
        count = conn.execute("SELECT COUNT(*) FROM candidates WHERE job_id = ?", (job['id'],)).fetchone()[0]
        job_labels.append(job['title'])
        job_counts.append(count)
        
    # 2. Score Distribution (e.g. 0-50, 51-75, 76-100)
    scores = conn.execute("SELECT total_score FROM candidates").fetchall()
    score_buckets = [0, 0, 0] # Low, Medium, High
    
    for s in scores:
        val = s['total_score']
        if val < 50: score_buckets[0] += 1
        elif val < 80: score_buckets[1] += 1
        else: score_buckets[2] += 1
        
    # 3. Pipeline Funnel (Status Counts)
    statuses = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected']
    status_counts = []
    for st in statuses:
        # Check for NULL status and treat as 'Applied' if st=='Applied'
        if st == 'Applied':
            c = conn.execute("SELECT COUNT(*) FROM candidates WHERE status = ? OR status IS NULL", (st,)).fetchone()[0]
        else:
            c = conn.execute("SELECT COUNT(*) FROM candidates WHERE status = ?", (st,)).fetchone()[0]
        status_counts.append(c)

    conn.close()
    
    return render_template('analytics.html', 
                           job_labels=job_labels, 
                           job_counts=job_counts,
                           score_buckets=score_buckets,
                           pipeline_labels=statuses,
                           pipeline_counts=status_counts)
