from flask import Blueprint, render_template
import database

bp = Blueprint('analytics', __name__)

@bp.route('/analytics')
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
        
    conn.close()
    
    return render_template('analytics.html', 
                           job_labels=job_labels, 
                           job_counts=job_counts,
                           score_buckets=score_buckets)
